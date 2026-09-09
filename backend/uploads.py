"""HTTP multipart handling and WhatsApp export processing."""

import io
import re
import zipfile

import storage

from gemini import classify_messages


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
    records = []
    current = None
    for raw_line in content.splitlines():
        line = raw_line.strip("\ufeff\u200e\u200f")
        match = LINE_RE.match(line)
        if match:
            if current:
                records.append(current)
            date_value = match.group("bracket_date") or match.group("plain_date")
            current = {
                "timestamp": _parse_date(date_value),
                "text": (match.group("bracket_text") or match.group("plain_text")).strip(),
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
    created = 0
    skipped = 0
    pending = []
    with storage.connect() as connection:
        for record in records:
            fingerprint = f"{record['timestamp'].isoformat()}:{record['text']}"
            exists = connection.execute(
                "SELECT id FROM sentiment_messages WHERE fingerprint = ?", (fingerprint,)
            )
            if exists.fetchone():
                skipped += 1
                continue
            pending.append((record, fingerprint))

        predictions = classify_messages([record["text"] for record, _ in pending])
        if len(predictions) != len(pending):
            raise RuntimeError("The classifier did not return one result per message")
        for (record, fingerprint), prediction in zip(pending, predictions):
            storage.insert_message(
                connection,
                record,
                prediction,
                fingerprint,
            )
            created += 1
        connection.commit()
    return {"created": created, "skipped": skipped, "total": len(records)}
