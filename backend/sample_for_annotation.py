"""Échantillonne un sous-ensemble de ``annotation_pool.jsonl`` à annoter.

Prélève un échantillon stratifié par source, pondéré vers le groupe cible
réel (UCB Bac 2 Informatique), filtre les messages trop courts ou trop longs
pour rester représentatifs d'un message de discussion typique, puis écrit le
résultat dans ``backend/annotation_sample.jsonl`` avec un identifiant stable
par ligne pour que les lots annotés puissent être recollés sans ambiguïté.

Utilisation :
    python backend/sample_for_annotation.py
"""

import json
import random

import settings


POOL_PATH = settings.BASE_DIR / "annotation_pool.jsonl"
OUTPUT_PATH = settings.BASE_DIR / "annotation_sample.jsonl"
SEED = 42
MIN_LENGTH = 2
MAX_LENGTH = 220

# Nombre de messages prélevés par source. Le groupe UCB Bac 2 Informatique
# est le groupe cible réel du projet et reçoit la part la plus importante ;
# les autres apportent de la diversité linguistique et de registre.
TARGETS = {
    "WhatsApp Chat - UCB Bac 2 Informatique 💻🖱️.zip": 500,
    "WhatsApp Chat with ⚽🏀🥊 🏋🏿_♀️🎱PRINCE OBIB🏈🎾🤼_♀️🛼🏸.zip": 300,
    "WhatsApp Chat with Product Team @Kelor Tech .zip": 100,
    "WhatsApp Chat with Promotion de la A6 19-20🚗.zip": 64,
}


def main():
    by_source = {source: [] for source in TARGETS}
    with POOL_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            text = row["text"]
            if not (MIN_LENGTH <= len(text) <= MAX_LENGTH):
                continue
            if row["source"] in by_source:
                by_source[row["source"]].append(text)

    rng = random.Random(SEED)
    sample = []
    for source, target in TARGETS.items():
        pool = by_source[source]
        rng.shuffle(pool)
        taken = pool[:target]
        sample.extend({"text": text, "source": source} for text in taken)
        print(f"{source}: {len(taken)} / {target} demandés ({len(pool)} disponibles)")

    rng.shuffle(sample)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(sample):
            handle.write(json.dumps({"id": index, **row}, ensure_ascii=False) + "\n")

    print(f"\n{len(sample)} messages écrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
