"""SEC EDGAR source: recent filings for the watchlist.

Uses two public, keyless endpoints:

  * https://www.sec.gov/files/company_tickers.json      ticker -> CIK map
  * https://data.sec.gov/submissions/CIK##########.json  recent filings

SEC fair-use rules: send a real contact in the User-Agent (set
PULSEBOARD_CONTACT) and keep request rates modest.
"""

import json
from pathlib import Path

import httpx

from pulseboard import config

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "edgar_sample.json"


def _headers():
    return {"User-Agent": config.USER_AGENT, "Accept-Encoding": "gzip"}


def ticker_to_cik(client, tickers):
    """Resolve tickers to CIK numbers using SEC's public map."""
    data = client.get(TICKER_MAP_URL, headers=_headers()).json()
    wanted = {t.upper() for t in tickers}
    out = {}
    for entry in data.values():
        if entry["ticker"].upper() in wanted:
            out[entry["ticker"].upper()] = (entry["cik_str"], entry["title"])
    return out


def parse_submissions(payload, company_name):
    """Turn one company's submissions JSON into normalised events."""
    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])
    cik = int(payload.get("cik", 0))

    events = []
    for form, date, accession, doc in zip(forms, dates, accessions, docs):
        if form not in config.INTERESTING_FORMS:
            continue
        acc_nodash = accession.replace("-", "")
        url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"
            if doc
            else f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
        )
        events.append(
            {
                "source": "edgar",
                "ref": accession,
                "company": company_name,
                "title": f"{company_name} filed a {form}",
                "detail": f"Form {form}",
                "date": date,
                "url": url,
            }
        )
    return events


def fetch(limit_per_company=8):
    """Fetch recent interesting filings for every watchlist company."""
    if config.OFFLINE:
        samples = json.loads(FIXTURE.read_text())
        events = []
        for name, payload in samples.items():
            events.extend(parse_submissions(payload, name)[:limit_per_company])
        return events

    events = []
    with httpx.Client(timeout=20) as client:
        ciks = ticker_to_cik(client, config.WATCHLIST)
        for ticker, (cik, title) in ciks.items():
            resp = client.get(SUBMISSIONS_URL.format(cik=cik), headers=_headers())
            resp.raise_for_status()
            events.extend(parse_submissions(resp.json(), title)[:limit_per_company])
    return events
