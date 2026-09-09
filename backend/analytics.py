"""Dashboard summary calculations."""

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


def summary_payload(days):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    rows = [(row, parse_timestamp(row["timestamp"])) for row in storage.fetch_messages(limit=100000)]
    current = [(row, timestamp) for row, timestamp in rows if timestamp >= since]
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

    dates = [(since.date() + timedelta(days=offset)).isoformat() for offset in range(days + 1)]
    trend = [{"date": day, **daily[day]} for day in dates]
    last_day = [(row, timestamp) for row, timestamp in current if timestamp >= now - timedelta(days=1)]
    negative_last_day = sum(1 for row, _ in last_day if row["sentiment"] == "negative")
    previous_start = since - timedelta(days=days)
    previous = [(row, timestamp) for row, timestamp in rows if previous_start <= timestamp < since]
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
        "period_days": days,
        "total_messages": len(current),
        "counts": {key: counts.get(key, 0) for key in ["positive", "neutral", "negative", "unknown"]},
        "negative_last_24h": negative_last_day,
        "negative_spike": spike,
        "alerts": alerts,
        "trend": trend,
        "emotions": [{"emotion": key, "count": value} for key, value in emotions.most_common()],
    }
