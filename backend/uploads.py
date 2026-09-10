"""Gestion des envois HTTP multipart et traitement des exports WhatsApp."""

import io
import re
import zipfile

import storage

from local_model import classify_messages


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_CHAT_TEXT_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024

LINE_RE = re.compile(
    r"^(?:\[(?P<bracket_date>[^\]]+)\]\s*(?P<bracket_author>[^:]+):\s?(?P<bracket_text>.*)"
    r"|(?P<plain_date>\d{1,4}[/-]\d{1,2}[/-]\d{1,4},\s+[^-]+)\s+-\s+"
    r"(?P<plain_author>[^:]+):\s?(?P<plain_text>.*))$"
)


def _parse_date(value):
    from datetime import datetime, timezone

    value = value.strip()
    formats = [
        "%d/%m/%y, %H:%M:%S", "%d/%m/%y, %H:%M",
        "%d/%m/%Y, %H:%M:%S", "%d/%m/%Y, %H:%M",
        "%d-%m-%y, %H:%M:%S", "%d-%m-%y, %H:%M",
        "%d-%m-%Y, %H:%M:%S", "%d-%m-%Y, %H:%M",
        "%m/%d/%y, %H:%M:%S", "%m/%d/%y, %H:%M",
        "%m/%d/%Y, %H:%M:%S", "%m/%d/%Y, %H:%M",
        "%m/%d/%y, %I:%M:%S %p", "%m/%d/%y, %I:%M %p",
        "%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y, %I:%M %p",
        "%d/%m/%y, %I:%M:%S %p", "%d/%m/%y, %I:%M %p",
    ]
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unsupported WhatsApp timestamp: {value}")


def parse_chat_export(content):
    """Découpe un export WhatsApp en enregistrements ``{"timestamp", "text"}``.

    Une ligne qui ressemble à un nouveau message mais porte une date que
    WhatsApp n'a en réalité pas produite (observé sur certains exports réels,
    par exemple un ``5/22, 10:51 AM`` tronqué) est ignorée plutôt que de faire
    échouer tout le fichier : une seule ligne mal formée ne doit pas faire
    perdre tous les autres messages de l'export.
    """
    records = []
    current = None
    for raw_line in content.splitlines():
        line = raw_line.strip("\ufeff\u200e\u200f")
        match = LINE_RE.match(line)
        if match:
            if current:
                records.append(current)
                current = None
            is_bracket_format = match.group("bracket_date") is not None
            date_value = match.group("bracket_date") if is_bracket_format else match.group("plain_date")
            text_value = match.group("bracket_text") if is_bracket_format else match.group("plain_text")
            try:
                timestamp = _parse_date(date_value)
            except ValueError:
                continue
            current = {
                "timestamp": timestamp,
                "text": (text_value or "").strip(),
            }
        elif current and line:
            current["text"] += f"\n{line}"
    if current:
        records.append(current)
    return [record for record in records if record["text"]]


def extract_chat_text(data, filename=""):
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload is too large; the maximum accepted size is 50 MB.")

    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = [
                info for info in archive.infolist()
                if not info.is_dir()
                and info.filename.lower().endswith(".txt")
                and not info.filename.startswith("__MACOSX/")
            ]
            if not entries:
                raise ValueError("The ZIP does not contain a WhatsApp chat text file.")
            if sum(info.file_size for info in archive.infolist()) > MAX_ARCHIVE_BYTES:
                raise ValueError("The uncompressed ZIP contents exceed the 100 MB safety limit.")
            selected = max(entries, key=lambda info: info.file_size)
            if selected.file_size > MAX_CHAT_TEXT_BYTES:
                raise ValueError("The chat text file exceeds the 25 MB safety limit.")
            data = archive.read(selected)

    if len(data) > MAX_CHAT_TEXT_BYTES:
        raise ValueError("The chat text file exceeds the 25 MB safety limit.")
    text = data.decode("utf-8-sig", errors="replace")
    return text


def import_records(records):
    with storage.connect() as connection:
        predictions = classify_messages([record["text"] for record in records])
        if len(predictions) != len(records):
            raise RuntimeError("The classifier did not return one result per message")
        for record, prediction in zip(records, predictions):
            storage.insert_message(connection, record, prediction)
        connection.commit()
    timestamps = [record["timestamp"] for record in records]
    return {
        "created": len(records),
        "total": len(records),
        "range": {"from": min(timestamps).isoformat(), "to": max(timestamps).isoformat()},
    }
