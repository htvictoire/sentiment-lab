"""Inférence de sentiment locale avec AfroXLMR.

Charge le classifieur entraîné par ``backend/train_model.py`` depuis
``settings.LOCAL_MODEL_PATH`` et expose ``classify_messages`` comme unique
point d'entrée utilisé par ``uploads.py``. Le modèle prédit uniquement le
sentiment (``positive``, ``neutral`` ou ``negative``) ; ``emotion`` et
``summary`` sont des valeurs d'affichage fixes par label, non déduites du
texte du message, et ``language`` n'est pas détecté et reste à sa valeur par
défaut. Ces champs sont conservés pour que la réponse de l'API garde la forme
déjà attendue par le tableau de bord.
"""

from dataclasses import asdict, dataclass

import settings


LABELS = ("positive", "neutral", "negative")
_MODEL = None
_TOKENIZER = None


@dataclass
class SentimentResult:
    label: str
    confidence: float
    language: str = "unknown"
    emotion: str = "neutral"
    summary: str = ""

    def model_dump(self):
        return asdict(self)


def is_model_ready():
    """Indique si un modèle entraîné est présent dans ``LOCAL_MODEL_PATH``."""
    model_path = settings.LOCAL_MODEL_PATH
    return (model_path / "config.json").is_file() and (
        (model_path / "model.safetensors").is_file()
        or (model_path / "pytorch_model.bin").is_file()
    )


def _presentation_fields(label):
    """Retourne le couple fixe ``(emotion, summary)`` affiché pour ``label``."""
    emotion = {
        "positive": "joy",
        "negative": "frustration",
        "neutral": "neutral",
    }.get(label, "neutral")
    summary = {
        "positive": "Tonalité positive détectée.",
        "negative": "Tonalité négative détectée.",
        "neutral": "Tonalité neutre détectée.",
    }.get(label, "Sentiment non déterminé.")
    return emotion, summary


def _load_model():
    """Charge et met en cache le modèle et le tokenizer pour l'inférence CPU.

    Lève ``RuntimeError`` si ``backend/train_model.py`` n'a pas encore produit
    de modèle dans ``LOCAL_MODEL_PATH``.
    """
    global _MODEL, _TOKENIZER
    if _MODEL is not None and _TOKENIZER is not None:
        return _MODEL, _TOKENIZER
    if not is_model_ready():
        raise RuntimeError(
            "Le modèle local n'est pas entraîné. Lancez d'abord backend/train_model.py."
        )

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_path = str(settings.LOCAL_MODEL_PATH)
    _TOKENIZER = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    _MODEL = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        local_files_only=True,
    )
    _MODEL.to(torch.device("cpu"))
    _MODEL.eval()
    return _MODEL, _TOKENIZER


def classify_messages(texts):
    """Classe ``texts`` avec le modèle local, par lots adaptés au CPU.

    Retourne un ``SentimentResult`` par texte d'entrée, dans le même ordre.
    Retourne une liste vide si l'entrée est vide. Lève ``RuntimeError`` si
    aucun modèle entraîné n'est disponible.
    """
    if not texts:
        return []

    import torch

    model, tokenizer = _load_model()
    predictions = []
    batch_size = max(1, settings.LOCAL_INFERENCE_BATCH_SIZE)
    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start:start + batch_size]
        encoded = tokenizer(
            batch_texts,
            max_length=128,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        with torch.inference_mode():
            probabilities = torch.softmax(model(**encoded).logits, dim=-1)
            confidences, indices = probabilities.max(dim=-1)

        for confidence, index in zip(confidences.tolist(), indices.tolist()):
            label = str(model.config.id2label.get(index, "unknown")).lower()
            if label not in LABELS:
                label = "unknown"
            emotion, summary = _presentation_fields(label)
            predictions.append(
                SentimentResult(
                    label=label,
                    confidence=float(confidence),
                    emotion=emotion,
                    summary=summary,
                )
            )
    return predictions
