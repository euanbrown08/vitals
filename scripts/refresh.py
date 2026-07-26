"""Pull the latest data from every source into the local database.

Usage:
    python -m scripts.refresh            # live APIs
    PULSEBOARD_OFFLINE=1 python -m scripts.refresh   # bundled sample data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pulseboard import config, store
from pulseboard.sources import clinicaltrials, edgar, news


def main():
    conn = store.connect(config.DB_PATH)
    total_new = 0
    for name, source in [("edgar", edgar), ("trials", clinicaltrials), ("news", news)]:
        try:
            events = source.fetch()
        except Exception as exc:  # noqa: BLE001 - a source failing shouldn't kill the rest
            print(f"[{name}] FAILED: {exc}")
            continue
        added = store.upsert_events(conn, events)
        total_new += added
        print(f"[{name}] {len(events)} fetched, {added} new")
    print(f"Done. {total_new} new events. Totals: {store.counts(conn)}")
    if config.OFFLINE:
        print("(offline mode — bundled sample data, not live)")


if __name__ == "__main__":
    main()
