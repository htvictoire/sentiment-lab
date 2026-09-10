"""Calculs de synthèse du tableau de bord."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import settings
import storage


def parse_timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def serialize_message(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "timestamp": row["timestamp"],
        "language": row["language"] or "",
        "sentiment": row["sentiment"] or "unknown",
        "confidence": row["confidence"] or 0.0,
        "emotion": row["emotion"] or "neutral",
        "summary": row["summary"] or "",
    }


def summary_payload(days=7, start=None, end=None):
    """Calcule la synthèse du tableau de bord sur une période donnée.

    Par défaut, la période couvre les ``days`` derniers jours avant
    l'instant présent. Si ``start`` et ``end`` (des ``datetime`` avec fuseau
    horaire) sont fournis, la synthèse porte sur cette plage explicite à la
    place : c'est nécessaire pour consulter une conversation importée dont
    les messages sont tous antérieurs à aujourd'hui, un cas que la fenêtre
    « derniers N jours » ne peut pas couvrir.
    """
    end_boundary = end or datetime.now(timezone.utc)
    start_boundary = start or (end_boundary - timedelta(days=days))
    span_days = max(0, (end_boundary.date() - start_boundary.date()).days)

    rows = [(row, parse_timestamp(row["timestamp"])) for row in storage.fetch_messages(limit=100000)]
    current = [(row, timestamp) for row, timestamp in rows if start_boundary <= timestamp <= end_boundary]
    counts = Counter(row["sentiment"] or "unknown" for row, _ in current)
    daily = defaultdict(lambda: {"messages": 0, "positive": 0, "neutral": 0, "negative": 0})
    emotions = Counter()

    for row, timestamp in current:
        day = timestamp.date().isoformat()
        label = row["sentiment"] or "unknown"
        daily[day]["messages"] += 1
        if label in daily[day]:
            daily[day][label] += 1
        emotions[row["emotion"] or "neutral"] += 1

    dates = [(start_boundary.date() + timedelta(days=offset)).isoformat() for offset in range(span_days + 1)]
    trend = [{"date": day, **daily[day]} for day in dates]
    last_day = [(row, timestamp) for row, timestamp in current if timestamp >= end_boundary - timedelta(days=1)]
    negative_last_day = sum(1 for row, _ in last_day if row["sentiment"] == "negative")
    previous_start = start_boundary - timedelta(days=span_days or days)
    previous = [(row, timestamp) for row, timestamp in rows if previous_start <= timestamp < start_boundary]
    previous_negative = sum(1 for row, _ in previous if row["sentiment"] == "negative")
    current_rate = negative_last_day / max(1, len(last_day))
    previous_rate = previous_negative / max(1, len(previous))
    spike = (
        current_rate >= settings.NEGATIVE_SPIKE_RATE
        and negative_last_day >= settings.NEGATIVE_SPIKE_MIN_MESSAGES
        and current_rate >= max(0.15, previous_rate * settings.NEGATIVE_SPIKE_MULTIPLIER)
    )
    alerts = []
    if spike:
        alerts.append({
            "kind": "negative_spike",
            "severity": "warning",
            "title": "Le sentiment négatif est élevé",
            "description": f"{negative_last_day} messages négatifs sont arrivés au cours des dernières 24 heures ({current_rate:.0%} des messages).",
        })
    return {
        "period_days": span_days if (start and end) else days,
        "range_start": start_boundary.date().isoformat(),
        "range_end": end_boundary.date().isoformat(),
        "total_messages": len(current),
        "counts": {key: counts.get(key, 0) for key in ["positive", "neutral", "negative", "unknown"]},
        "negative_last_24h": negative_last_day,
        "negative_spike": spike,
        "alerts": alerts,
        "trend": trend,
        "emotions": [{"emotion": key, "count": value} for key, value in emotions.most_common()],
    }
