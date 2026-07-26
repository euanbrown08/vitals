from pulseboard import store


def _event(ref, source="news", date="2026-07-20"):
    return {
        "source": source,
        "ref": ref,
        "company": "Test Co",
        "title": f"Event {ref}",
        "detail": "detail",
        "date": date,
        "url": f"https://example.com/{ref}",
    }


def test_upsert_dedupes_on_source_and_ref(tmp_path):
    conn = store.connect(tmp_path / "t.db")
    added = store.upsert_events(conn, [_event("a"), _event("b")])
    assert added == 2
    # Same refs again: nothing new. Same ref, different source: new row.
    added = store.upsert_events(conn, [_event("a"), _event("a", source="edgar")])
    assert added == 1
    assert store.counts(conn) == {"news": 2, "edgar": 1}


def test_latest_orders_by_date_desc(tmp_path):
    conn = store.connect(tmp_path / "t.db")
    store.upsert_events(
        conn,
        [_event("old", date="2026-06-01"), _event("new", date="2026-07-25")],
    )
    rows = store.latest(conn)
    assert [r["ref"] for r in rows] == ["new", "old"]
    assert store.latest(conn, source="edgar") == []
