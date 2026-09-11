"""Échantillonne un lot supplémentaire de messages à dominante française.

Le français est la langue principale du groupe cible (UCB Bac 2 Informatique)
mais était sous-représenté dans le premier échantillon annoté (environ 27 %
d'après un comptage heuristique). Ce script sélectionne, dans
``annotation_pool.jsonl``, des messages dont le décompte de mots-outils
français dépasse celui des marqueurs swahili (Bukavu compris), en excluant les
messages déjà présents dans ``training_data.jsonl``, puis écrit le résultat
dans ``backend/annotation_sample_fr.jsonl`` pour une nouvelle passe
d'annotation.

Utilisation :
    python backend/sample_more_french.py
"""

import json
import random
import re

import settings


POOL_PATH = settings.BASE_DIR / "annotation_pool.jsonl"
TRAINING_PATH = settings.TRAINING_DATA_PATH
OUTPUT_PATH = settings.BASE_DIR / "annotation_sample_fr.jsonl"
SEED = 43
MIN_LENGTH = 2
MAX_LENGTH = 220

FRENCH_WORDS = set(
    "le la les de des du un une et est dans avec pour que qui pas ne vous nous "
    "tu il elle on sont sera était être avoir mais ou si comme plus très bien "
    "bon bonne merci alors donc quoi encore déjà aussi non oui ce cette ces "
    "mon ma mes ton ta tes son sa ses notre votre leur leurs quand comment "
    "pourquoi car ici là parce entre chez sans sur au aux toi moi lui eux nos "
    "vos peut faire fait faut veux veut peux dois doit va vais vas allons "
    "allez vont était étions étiez étaient serai seras serons serez seraient "
    "jamais toujours parfois beaucoup peu trop assez cela ça cet après avant "
    "pendant depuis vers chaque tout tous toute toutes rien personne quelque "
    "quelques".split()
)
SWAHILI_WORDS = set(
    "ni na ya wa ku mu bya ba njo kwa sana tuko una mina niko aiko iko akuna "
    "sasa kesho jana leo weye miye shiye bengine muna tuna bana bata baba "
    "mama kaka yaya mzuri poa kaza wapi ile ilo ivi vile aye owaka kbs kbsa "
    "habari asante".split()
)

# Nombre de messages français prélevés par source, dans l'ordre de priorité
# du groupe cible réel du projet.
TARGETS = {
    "WhatsApp Chat - UCB Bac 2 Informatique 💻🖱️.zip": 400,
    "WhatsApp Chat with ⚽🏀🥊 🏋🏿_♀️🎱PRINCE OBIB🏈🎾🤼_♀️🛼🏸.zip": 150,
    "WhatsApp Chat with Product Team @Kelor Tech .zip": 54,
}


def french_score(text):
    words = re.findall(r"[a-zàâäéèêëïîôöùûüç']+", text.lower())
    french = sum(1 for word in words if word in FRENCH_WORDS)
    swahili = sum(1 for word in words if word in SWAHILI_WORDS)
    return french, swahili


def main():
    existing = {json.loads(line)["text"] for line in TRAINING_PATH.open("r", encoding="utf-8")}

    by_source = {source: [] for source in TARGETS}
    with POOL_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            text = row["text"]
            if text in existing or row["source"] not in by_source:
                continue
            if not (MIN_LENGTH <= len(text) <= MAX_LENGTH):
                continue
            french, swahili = french_score(text)
            if french >= 1 and french > swahili:
                by_source[row["source"]].append(text)

    rng = random.Random(SEED)
    sample = []
    for source, target in TARGETS.items():
        pool = by_source[source]
        rng.shuffle(pool)
        taken = pool[:target]
        sample.extend({"text": text, "source": source} for text in taken)
        print(f"{source}: {len(taken)} / {target} demandés ({len(pool)} candidats français)")

    rng.shuffle(sample)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(sample):
            handle.write(json.dumps({"id": index, **row}, ensure_ascii=False) + "\n")

    print(f"\n{len(sample)} messages écrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
