"""Stockage SQLite des messages importés et classés."""

import sqlite3

import settings


def connect():
    connection = sqlite3.connect(settings.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sentiment_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sentiment TEXT NOT NULL DEFAULT 'unknown',
                confidence REAL NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT 'unknown',
                emotion TEXT NOT NULL DEFAULT 'neutral',
                summary TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS sentiment_messages_timestamp_idx
                ON sentiment_messages(timestamp);
            """
        )


def insert_message(connection, record, prediction):
    connection.execute(
        """
        INSERT INTO sentiment_messages
            (text, timestamp, sentiment, confidence, language, emotion, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["text"],
            record["timestamp"].isoformat(),
            prediction.label,
            prediction.confidence,
            prediction.language,
            prediction.emotion,
            prediction.summary,
        ),
    )


def clear_messages():
    with connect() as connection:
        connection.execute("DELETE FROM sentiment_messages")
        connection.commit()


def fetch_messages(limit=100, label="", query=""):
    clauses = []
    values = []
    if label:
        clauses.append("sentiment = ?")
        values.append(label)
    if query:
        clauses.append("text LIKE ?")
        values.append(f"%{query}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as connection:
        return connection.execute(
            f"SELECT id, text, timestamp, sentiment, confidence, language, emotion, summary "
            f"FROM sentiment_messages {where} ORDER BY timestamp DESC LIMIT ?",
            [*values, limit],
        ).fetchall()
