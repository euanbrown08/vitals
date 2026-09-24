import json
from pathlib import Path

from vitals.sources import clinicaltrials, edgar, news

FIXTURES = Path(__file__).parent / "fixtures"

EVENT_KEYS = {"source", "ref", "company", "title", "detail", "date", "url"}


def test_edgar_parse_filters_and_normalises():
    payload = json.loads((FIXTURES / "edgar_sample.json").read_text())["Example Health Inc"]
    events = edgar.parse_submissions(payload, "Example Health Inc")
    # Forms 3 and 4 (insider ownership) must be filtered out.
    assert len(events) == 3
    assert {e["detail"] for e in events} == {"Form 8-K", "Form 10-Q", "Form S-1"}
    for e in events:
        assert set(e) == EVENT_KEYS
        assert e["source"] == "edgar"
        assert e["url"].startswith("https://www.sec.gov/Archives/edgar/data/1111111/")


def test_trials_parse_normalises_phase_and_status():
    payload = json.loads((FIXTURES / "trials_sample.json").read_text())["digital therapeutic"]
    events = clinicaltrials.parse_studies(payload, "digital therapeutic")
    assert len(events) == 2
    by_id = {e["url"]: e for e in events}
    e = by_id["https://clinicaltrials.gov/study/NCT00000002"]
    assert "Phase 2" in e["detail"]
    assert "Active Not Recruiting" in e["detail"]
    assert e["date"] == "2026-07-18"


def test_news_parse_keyword_filter():
    xml_text = (FIXTURES / "news_sample.xml").read_text()
    events = news.parse_feed(xml_text, "sample-feed")
    titles = [e["title"] for e in events]
    # Three funding items kept, the non-funding roundup dropped.
    assert len(events) == 3
    assert all("raises" in t or "raise" in t.lower() for t in titles)
    assert events[0]["date"] == "2026-07-15"


def test_news_parse_survives_bad_xml():
    assert news.parse_feed("<not really xml", "feed") == []
