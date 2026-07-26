"""SQLite persistence for normalised events.

Every source produces "events" with the same shape, so the dashboard can
merge them into one catalyst feed:

    {
        "ref":     unique id within the source (used to dedupe),
        "source":  "edgar" | "trials" | "news",
        "company": company / sponsor / publisher name,
        "title":   short human-readable headline,
        "detail":  secondary line (form type, phase, feed name...),
        "date":    ISO date string (YYYY-MM-DD),
        "url":     link to the primary source,
    }
"""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id       INTEGER PRIMARY KEY,
    source   TEXT NOT NULL,
    ref      TEXT NOT NULL,
    company  TEXT,
    title    TEXT NOT NULL,
    detail   TEXT,
    date     TEXT,
    url      TEXT,
    inserted_at TEXT DEFAULT (datetime('now')),
    UNIQUE (source, ref)
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events (date DESC);
"""


def connect(db_path):
    """Open (and if needed initialise) the database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_events(conn, events):
    """Insert events, silently skipping ones already stored.

    Returns the number of newly inserted rows.
    """
    before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.executemany(
        """INSERT OR IGNORE INTO events (source, ref, company, title, detail, date, url)
           VALUES (:source, :ref, :company, :title, :detail, :date, :url)""",
        events,
    )
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    return after - before


def latest(conn, source=None, limit=50):
    """Most recent events, optionally filtered to one source."""
    if source:
        rows = conn.execute(
            "SELECT * FROM events WHERE source = ? ORDER BY date DESC, id DESC LIMIT ?",
            (source, limit),
        )
    else:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        )
    return [dict(r) for r in rows]


def counts(conn):
    """Event totals per source, e.g. {"edgar": 12, "trials": 25, "news": 9}."""
    rows = conn.execute("SELECT source, COUNT(*) AS n FROM events GROUP BY source")
    return {r["source"]: r["n"] for r in rows}
