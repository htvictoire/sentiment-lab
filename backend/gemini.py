"""Gemini-backed multilingual sentiment classification."""

import json
import logging
import math
from dataclasses import asdict, dataclass

import settings


logger = logging.getLogger(__name__)


LABELS = {"positive", "neutral", "negative", "unknown"}
EMOTIONS = {
    "joy", "gratitude", "excitement", "anger", "sadness", "frustration",
    "confusion", "neutral", "other",
}


@dataclass
class SentimentResult:
    label: str
    confidence: float
    language: str = "unknown"
    emotion: str = "neutral"
    summary: str = ""

    def model_dump(self):
        return asdict(self)


def _validated_result(payload):
    if not isinstance(payload, dict):
        raise ValueError("Gemini response must be a JSON object")

    label = payload.get("label")
    if label not in LABELS:
        raise ValueError("Gemini returned an invalid sentiment label")

    confidence = payload.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("Gemini returned an invalid confidence value")
    confidence = float(confidence)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("Gemini confidence must be between 0 and 1")

    language = payload.get("language", "unknown")
    emotion = payload.get("emotion", "neutral")
    summary = payload.get("summary", "")
    if not isinstance(language, str) or not isinstance(emotion, str) or not isinstance(summary, str):
        raise ValueError("Gemini returned invalid text fields")
    if emotion not in EMOTIONS:
        raise ValueError("Gemini returned an invalid emotion")
    if len(language) > 32 or len(summary) > 500:
        raise ValueError("Gemini returned an oversized text field")

    return SentimentResult(
        label=label,
        confidence=confidence,
        language=language,
        emotion="neutral" if label == "neutral" else emotion,
        summary=summary,
    )


def _fallback_result(text: str) -> SentimentResult:
    if not text.strip():
        return SentimentResult(label="unknown", confidence=0.0, summary="Empty message")
    return SentimentResult(
        label="unknown",
        confidence=0.0,
        emotion="neutral",
        summary="Gemini is not configured; this message was stored without classification.",
    )


def _classify_batch(client, texts):
    numbered_messages = "\n\n".join(
        f"Message {index}:\n{text}" for index, text in enumerate(texts)
    )
    prompt = f"""
You are a multilingual sentiment classifier for a WhatsApp group.

Classify every message into exactly one label:
- positive: approval, happiness, praise, excitement, gratitude, or encouragement
- neutral: factual information, greetings, questions, or text with no clear sentiment
- negative: complaint, anger, disappointment, criticism, sadness, or hostility
- unknown: unreadable, empty, or impossible to classify

For every message, detect the language or language mix. Messages may contain
French, English, Swahili, slang, abbreviations, emojis, or code-switching.
Do not infer sentiment about the sender as a person. Classify only the message.
Also classify the dominant emotion as one of: joy, gratitude, excitement, anger,
sadness, frustration, confusion, neutral, or other.
Write a short summary in French, with at most 12 words.

Return only valid JSON in exactly this shape:
{{"results":[{{"id":0,"label":"positive","confidence":0.95,"language":"fr","emotion":"joy","summary":"Message encourageant."}}]}}
Include exactly one result for every message, preserving its id.

Messages:
{numbered_messages}
"""

    from google.genai import types

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
            max_output_tokens=4096,
        ),
    )

    try:
        payload = json.loads(response.text)
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list) or len(results) != len(texts):
            raise ValueError("Gemini returned an unexpected batch size")

        indexed = {}
        for item in results:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ValueError("Gemini returned an invalid message id")
            if item["id"] in indexed:
                raise ValueError("Gemini returned duplicate message ids")
            indexed[item["id"]] = _validated_result(item)

        if set(indexed) != set(range(len(texts))):
            raise ValueError("Gemini did not classify every message")
        return [indexed[index] for index in range(len(texts))]
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("Gemini returned an invalid sentiment batch: %s", exc)
        raise RuntimeError("Gemini returned an invalid classification batch") from exc


def classify_messages(texts):
    """Classify messages in bounded batches to reduce repeated prompt tokens."""
    if not texts:
        return []
    if not settings.GEMINI_API_KEY:
        if settings.DEMO_MODE:
            return [_fallback_result(text) for text in texts]
        raise RuntimeError("GEMINI_API_KEY is not configured")

    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    batch_size = max(1, settings.GEMINI_BATCH_SIZE)
    predictions = []
    for start in range(0, len(texts), batch_size):
        predictions.extend(_classify_batch(client, texts[start:start + batch_size]))
    return predictions


def classify_message(text: str) -> SentimentResult:
    """Classify one message through the same batched implementation."""
    return classify_messages([text])[0]
