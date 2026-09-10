"""Entraîne AfroXLMR-small en classifieur de sentiment local.

Format d'entrée : ``backend/training_data.jsonl``, un objet JSON par ligne
avec un champ ``text`` et un champ ``label``. ``label`` doit valoir
``positive``, ``neutral`` ou ``negative``. Au moins trois exemples par label
sont requis, car les données sont réparties en trois ensembles
(entraînement, validation, test).

Sortie : le modèle entraîné et son tokenizer sont écrits dans
``settings.LOCAL_MODEL_PATH``, avec un fichier ``training_metadata.json``
qui enregistre les hyperparamètres et les métriques d'évaluation de la run.

Utilisation :
    python backend/train_model.py
    python backend/train_model.py --epochs 5 --batch-size 16
    python backend/train_model.py --full-fine-tune
"""

import argparse
import json
import random
from collections import Counter, defaultdict

import settings


LABELS = ("positive", "neutral", "negative")
MIN_EXAMPLES_PER_LABEL = 3


def read_examples(path):
    """Charge et valide le fichier d'entraînement JSONL situé à ``path``.

    Retourne une liste de dictionnaires ``{"text": str, "label": str}``. Lève
    ``ValueError`` en cas de JSON mal formé, de ``text`` manquant ou vide, de
    label hors de ``LABELS``, ou d'un label comptant moins de
    ``MIN_EXAMPLES_PER_LABEL`` exemples.
    """
    examples = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}.") from exc
            text = item.get("text") if isinstance(item, dict) else None
            label = item.get("label") if isinstance(item, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Missing text on line {line_number}.")
            if label not in LABELS:
                raise ValueError(f"Invalid label on line {line_number}: {label!r}.")
            examples.append({"text": text.strip(), "label": label})

    counts = Counter(item["label"] for item in examples)
    missing = [label for label in LABELS if counts[label] < MIN_EXAMPLES_PER_LABEL]
    if missing:
        raise ValueError(
            f"At least {MIN_EXAMPLES_PER_LABEL} examples are required for each label: "
            + ", ".join(missing)
        )
    return examples


def split_examples(examples, validation_ratio, test_ratio, seed):
    """Répartit ``examples`` en ensembles d'entraînement, de validation et de test, par label.

    Chaque label est mélangé et découpé indépendamment, afin que chaque
    ensemble garde le même équilibre de labels que les données source.
    ``validation_ratio`` et ``test_ratio`` s'appliquent par label et sont
    arrondis à au moins un exemple chacun, le reste allant à l'entraînement.
    Lève ``ValueError`` si un label n'a pas assez d'exemples pour laisser au
    moins un exemple à l'entraînement.
    """
    groups = defaultdict(list)
    for example in examples:
        groups[example["label"]].append(example)

    rng = random.Random(seed)
    train, validation, test = [], [], []
    for label in LABELS:
        group = groups[label]
        rng.shuffle(group)
        size = len(group)
        test_size = max(1, round(size * test_ratio))
        validation_size = max(1, round(size * validation_ratio))
        if test_size + validation_size >= size:
            raise ValueError(
                f"Not enough examples for label {label!r} to fill train, validation "
                "and test splits; add more training data."
            )
        test.extend(group[:test_size])
        validation.extend(group[test_size:test_size + validation_size])
        train.extend(group[test_size + validation_size:])

    rng.shuffle(train)
    rng.shuffle(validation)
    rng.shuffle(test)
    return train, validation, test


def metrics(predictions, expected):
    """Calcule l'exactitude et le F1 macro entre labels prédits et attendus."""
    accuracy = sum(prediction == actual for prediction, actual in zip(predictions, expected)) / len(expected)
    f1_scores = []
    for label in LABELS:
        true_positive = sum(prediction == label and actual == label for prediction, actual in zip(predictions, expected))
        false_positive = sum(prediction == label and actual != label for prediction, actual in zip(predictions, expected))
        false_negative = sum(prediction != label and actual == label for prediction, actual in zip(predictions, expected))
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1_scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return {"accuracy": accuracy, "macro_f1": sum(f1_scores) / len(f1_scores)}


def evaluate(model, tokenizer, examples, torch, device, max_length, batch_size=8):
    """Exécute l'inférence sur ``examples`` et retourne exactitude et F1 macro."""
    model.eval()
    predictions, expected = [], []
    with torch.inference_mode():
        for start in range(0, len(examples), batch_size):
            batch = examples[start:start + batch_size]
            encoded = tokenizer(
                [item["text"] for item in batch],
                max_length=max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(device)
            output = model(**encoded).logits.argmax(dim=-1).tolist()
            predictions.extend(LABELS[index] for index in output)
            expected.extend(item["label"] for item in batch)
    return metrics(predictions, expected)


def train(args):
    """Exécute un entraînement complet et écrit le modèle et ses métadonnées sur disque."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    data_path = settings.TRAINING_DATA_PATH
    output_path = settings.LOCAL_MODEL_PATH
    learning_rate = args.learning_rate
    if learning_rate is None:
        # 2e-5 (le défaut habituel pour affiner un transformeur déjà entraîné)
        # est beaucoup trop faible pour entraîner une tête de classification
        # initialisée aléatoirement sur des caractéristiques gelées : la perte
        # stagne et le modèle s'effondre sur la classe majoritaire. Une tête
        # entraînée seule a besoin d'un taux d'apprentissage bien plus élevé.
        learning_rate = 2e-5 if args.full_fine_tune else 1e-3
    examples = read_examples(data_path)
    train_examples, validation_examples, test_examples = split_examples(
        examples, args.validation_ratio, args.test_ratio, args.seed
    )
    label_to_id = {label: index for index, label in enumerate(LABELS)}
    id_to_label = {index: label for label, index in label_to_id.items()}

    torch.manual_seed(args.seed)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
    device = torch.device("cpu")
    tokenizer = AutoTokenizer.from_pretrained(settings.LOCAL_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        settings.LOCAL_MODEL_NAME,
        num_labels=len(LABELS),
        id2label=id_to_label,
        label2id=label_to_id,
    ).to(device)

    if not args.full_fine_tune:
        for parameter in model.base_model.parameters():
            parameter.requires_grad = False

    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable_parameters, lr=learning_rate)
    model.train()
    train_labels = torch.tensor([label_to_id[item["label"]] for item in train_examples])
    train_indices = list(range(len(train_examples)))

    # Le jeu de données n'est pas équilibré entre labels (ex. beaucoup plus
    # de messages neutres que négatifs). Sans pondération, la perte non
    # pondérée récompense un modèle qui prédit toujours la classe majoritaire
    # puisque cela minimise déjà la perte moyenne. Chaque classe est donc
    # pondérée par l'inverse de sa fréquence, pour que se tromper sur une
    # classe rare coûte autant que se tromper sur la classe majoritaire.
    label_counts = Counter(item["label"] for item in train_examples)
    class_weights = torch.tensor(
        [len(train_examples) / (len(LABELS) * label_counts[label]) for label in LABELS],
        dtype=torch.float32,
    ).to(device)
    loss_function = torch.nn.CrossEntropyLoss(weight=class_weights)

    # Le F1 macro de validation est réévalué après chaque époque et le
    # meilleur point de contrôle est conservé sur disque : au-delà de
    # quelques époques, la perte d'entraînement continue de baisser (le
    # modèle mémorise) alors que les performances de validation stagnent ou
    # se dégradent. Sans ce suivi, un nombre d'époques trop généreux
    # écraserait un bon point de contrôle par un modèle en surapprentissage.
    output_path.mkdir(parents=True, exist_ok=True)
    best_macro_f1 = -1.0
    best_epoch = 0
    for epoch in range(args.epochs):
        random.Random(args.seed + epoch).shuffle(train_indices)
        batches = DataLoader(train_indices, batch_size=args.batch_size, shuffle=False)
        total_loss = 0.0
        model.train()
        for index_batch in batches:
            batch = [train_examples[index] for index in index_batch.tolist()]
            encoded = tokenizer(
                [item["text"] for item in batch],
                max_length=args.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(device)
            labels = train_labels[index_batch].to(device)
            optimizer.zero_grad()
            logits = model(**encoded).logits
            loss = loss_function(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss)

        epoch_validation = evaluate(model, tokenizer, validation_examples, torch, device, args.max_length)
        print(
            f"Époque {epoch + 1}/{args.epochs} · perte moyenne : {total_loss / len(batches):.4f} "
            f"· F1 macro validation : {epoch_validation['macro_f1']:.4f}"
        )
        if epoch_validation["macro_f1"] > best_macro_f1:
            best_macro_f1 = epoch_validation["macro_f1"]
            best_epoch = epoch + 1
            model.save_pretrained(output_path)
            tokenizer.save_pretrained(output_path)

    # Recharge le meilleur point de contrôle (et non celui de la dernière
    # époque) pour calculer les métriques finales rapportées.
    model = AutoModelForSequenceClassification.from_pretrained(
        output_path, local_files_only=True
    ).to(device)
    validation_metrics = evaluate(model, tokenizer, validation_examples, torch, device, args.max_length)
    test_metrics = evaluate(model, tokenizer, test_examples, torch, device, args.max_length)

    metadata = {
        "base_model": settings.LOCAL_MODEL_NAME,
        "labels": list(LABELS),
        "training_examples": len(train_examples),
        "validation_examples": len(validation_examples),
        "test_examples": len(test_examples),
        "validation": validation_metrics,
        "test": test_metrics,
        "epochs": args.epochs,
        "best_epoch": best_epoch,
        "batch_size": args.batch_size,
        "max_length": args.max_length,
        "learning_rate": learning_rate,
        "full_fine_tune": args.full_fine_tune,
    }
    (output_path / "training_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Entraîner le classifieur de sentiment AfroXLMR-small.")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument(
        "--learning-rate", type=float, default=None,
        help="par défaut 1e-3 (tête seule) ou 2e-5 (--full-fine-tune)",
    )
    parser.add_argument("--validation-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--full-fine-tune", action="store_true")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.max_length < 8:
        parser.error("epochs, batch-size et max-length doivent être positifs.")
    if args.validation_ratio <= 0 or args.test_ratio <= 0 or args.validation_ratio + args.test_ratio >= 1:
        parser.error("validation-ratio et test-ratio doivent être positifs et leur somme inférieure à 1.")
    train(args)


if __name__ == "__main__":
    main()
