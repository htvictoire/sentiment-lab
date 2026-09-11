"""Transforme les exports WhatsApp bruts en un réservoir de messages à annoter.

Lit chaque ``.zip`` de ``backend/raw_exports/``, en extrait le texte de
conversation avec le même analyseur que l'API (``uploads.extract_chat_text``
et ``parse_chat_export``), puis élimine les lignes système de WhatsApp
(médias omis, événements d'appartenance au groupe, avis de chiffrement,
marqueurs d'édition) ainsi que les doublons exacts. Le résultat est écrit
dans ``backend/annotation_pool.jsonl``, un objet JSON par ligne avec un champ
``text`` et un champ ``source`` (le nom du fichier d'export, conservé pour
savoir de quel groupe provient chaque message pendant l'annotation).

Ce script n'attribue aucun label de sentiment. L'annotation est une étape
manuelle séparée : recopier les lignes de ``annotation_pool.jsonl`` dans
``backend/training_data.jsonl`` en ajoutant un champ ``label``
(``positive``, ``neutral`` ou ``negative``).

Utilisation :
    python backend/prepare_training_data.py
"""

import json
import re
import zipfile

import settings
from uploads import extract_chat_text, parse_chat_export


RAW_EXPORTS_DIR = settings.BASE_DIR / "raw_exports"
OUTPUT_PATH = settings.BASE_DIR / "annotation_pool.jsonl"

# Avis système et espaces réservés aux médias de WhatsApp. Ils ne portent
# aucun sentiment et ne doivent pas entrer dans le réservoir d'entraînement.
# Comparaison insensible à la casse sur le texte complet du message.
SYSTEM_PATTERNS = [
    r"messages and calls are end-to-end encrypted",
    r"created (this )?group",
    r"created group",
    r"you created this group",
    r"added\b",
    r"removed\b",
    r"left$",
    r"changed the subject to",
    r"changed the group name to",
    r"changed this group'?s icon",
    r"changed their phone number",
    r"changed to\b",
    r"disappearing messages were turned (on|off)",
    r"security code changed",
    r"this message was deleted",
    r"you deleted this message",
    r"^image omitted$",
    r"^video omitted$",
    r"^audio omitted$",
    r"^gif omitted$",
    r"^sticker omitted$",
    r"^document omitted$",
    r"^contact card omitted$",
    r"<media omitted>",
    r"^null$",
]
SYSTEM_RE = re.compile("|".join(SYSTEM_PATTERNS), re.IGNORECASE)

# Marques de largeur nulle et mention « message modifié » que WhatsApp ajoute
# en ligne à des messages par ailleurs réels ; retirées plutôt que de
# provoquer le rejet du message entier.
INLINE_NOISE_RE = re.compile(
    r"[‎‏﻿]|<this message was edited>", re.IGNORECASE
)


def clean_text(text):
    text = INLINE_NOISE_RE.sub("", text)
    return text.strip()


def is_usable(text):
    if not text:
        return False
    if SYSTEM_RE.search(text):
        return False
    # Une ligne composée uniquement de mentions ou de ponctuation ne porte
    # aucun contenu classifiable.
    if not re.search(r"[^\W\d_]", text, re.UNICODE):
        return False
    return True


def extract_pool_entries(zip_path):
    data = zip_path.read_bytes()
    try:
        content = extract_chat_text(data, zip_path.name)
    except (ValueError, zipfile.BadZipFile) as exc:
        print(f"  Ignoré ({exc})")
        return []
    records = parse_chat_export(content)
    entries = []
    for record in records:
        text = clean_text(record["text"])
        if is_usable(text):
            entries.append({"text": text, "source": zip_path.name})
    return entries


def main():
    if not RAW_EXPORTS_DIR.is_dir():
        raise SystemExit(f"Dossier introuvable : {RAW_EXPORTS_DIR}")

    zip_paths = sorted(RAW_EXPORTS_DIR.glob("*.zip"))
    if not zip_paths:
        raise SystemExit(f"Aucun export .zip trouvé dans {RAW_EXPORTS_DIR}")

    seen = set()
    pool = []
    for zip_path in zip_paths:
        print(f"Lecture de {zip_path.name}")
        entries = extract_pool_entries(zip_path)
        added = 0
        for entry in entries:
            if entry["text"] in seen:
                continue
            seen.add(entry["text"])
            pool.append(entry)
            added += 1
        print(f"  {len(entries)} messages exploitables, {added} nouveaux après déduplication")

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for entry in pool:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n{len(pool)} messages écrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
