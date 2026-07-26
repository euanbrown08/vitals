"""Funding-news source: keyword-filtered items from healthtech RSS feeds.

Parsed with the standard library (xml.etree) — RSS 2.0 is simple enough
that a dedicated dependency isn't worth it.
"""

import email.utils
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from pulseboard import config

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "news_sample.xml"


def _norm_date(value):
    """RFC 2822 pubDate -> YYYY-MM-DD (falls back to the raw string)."""
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return value[:10]


def _matches(text):
    lowered = text.lower()
    return any(k in lowered for k in config.NEWS_KEYWORDS)


def parse_feed(xml_text, feed_name):
    """Turn one RSS 2.0 document into normalised events (keyword-filtered)."""
    events = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return events

    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if not title or not _matches(title + " " + desc):
            continue
        events.append(
            {
                "source": "news",
                "ref": link or title,
                "company": feed_name,
                "title": title,
                "detail": feed_name,
                "date": _norm_date(item.findtext("pubDate")),
                "url": link,
            }
        )
    return events


def _feed_name(url):
    return url.split("/")[2].removeprefix("www.")


def fetch():
    """Fetch and filter every configured feed. Feeds that error are skipped."""
    if config.OFFLINE:
        return parse_feed(FIXTURE.read_text(), "sample-feed")

    events = []
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        for url in config.FEEDS:
            try:
                resp = client.get(url, headers={"User-Agent": config.USER_AGENT})
                resp.raise_for_status()
            except httpx.HTTPError:
                continue  # a dead feed shouldn't kill the refresh
            events.extend(parse_feed(resp.text, _feed_name(url)))
    return events
