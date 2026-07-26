"""Central configuration: the watchlist, trial search terms and news feeds.

Everything here is meant to be edited. The defaults are a starter set of
US-listed healthtech / digital-health names.
"""

import os

# Public healthtech companies to follow on SEC EDGAR, by ticker.
WATCHLIST = [
    "HIMS",   # Hims & Hers Health
    "TDOC",   # Teladoc Health
    "IRTC",   # iRhythm Technologies
    "BFLY",   # Butterfly Network
    "PGNY",   # Progyny
    "PHR",    # Phreesia
    "OM",     # Outset Medical
    "TMDX",   # TransMedics
    "DOCS",   # Doximity
]

# Filing types worth surfacing (ownership forms like 3/4/5 are noise here).
INTERESTING_FORMS = {
    "8-K", "10-Q", "10-K", "10-K/A", "S-1", "S-1/A", "424B4", "424B5",
    "6-K", "SC 13D", "SC 13G", "DEF 14A",
}

# Search terms for ClinicalTrials.gov (each queried separately).
TRIAL_TERMS = [
    "digital therapeutic",
    "remote patient monitoring",
    "artificial intelligence diagnosis",
]

# RSS feeds scanned for funding/deal news.
FEEDS = [
    "https://www.fiercehealthcare.com/rss/xml",
    "https://www.mobihealthnews.com/feed",
    "https://techcrunch.com/category/health/feed/",
]

# An RSS item must match at least one keyword to be kept.
NEWS_KEYWORDS = [
    "raises", "raise", "funding", "series a", "series b", "series c",
    "seed round", "seed funding", "acquires", "acquisition", "merger",
    "ipo", "valuation", "venture",
]

# SEC asks API users to identify themselves. Set PULSEBOARD_CONTACT to your
# email before running a live refresh.
USER_AGENT = "pulseboard/0.1 ({})".format(
    os.environ.get("PULSEBOARD_CONTACT", "contact-not-set@example.com")
)

# When PULSEBOARD_OFFLINE=1, sources read bundled fixture data instead of
# calling the live APIs. Used for tests and offline demos.
OFFLINE = os.environ.get("PULSEBOARD_OFFLINE") == "1"

DB_PATH = os.environ.get("PULSEBOARD_DB", "pulseboard.db")
