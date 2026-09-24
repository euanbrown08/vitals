"""ClinicalTrials.gov source: recently-updated studies for tracked topics.

Uses the public v2 API: https://clinicaltrials.gov/api/v2/studies
"""

import json
from pathlib import Path

import httpx

from vitals import config

API_URL = "https://clinicaltrials.gov/api/v2/studies"

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "trials_sample.json"


def parse_studies(payload, term):
    """Turn a v2 /studies response into normalised events."""
    events = []
    for study in payload.get("studies", []):
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        sponsor = (
            proto.get("sponsorCollaboratorsModule", {})
            .get("leadSponsor", {})
            .get("name", "Unknown sponsor")
        )
        nct_id = ident.get("nctId")
        if not nct_id:
            continue
        phases = design.get("phases") or []
        phase = ", ".join(p.replace("PHASE", "Phase ") for p in phases) or "N/A"
        events.append(
            {
                "source": "trials",
                "ref": f"{nct_id}:{status.get('lastUpdatePostDateStruct', {}).get('date', '')}",
                "company": sponsor,
                "title": ident.get("briefTitle", nct_id),
                "detail": f"{status.get('overallStatus', 'UNKNOWN').title().replace('_', ' ')} · {phase} · {term}",
                "date": status.get("lastUpdatePostDateStruct", {}).get("date"),
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            }
        )
    return events


def fetch(page_size=15):
    """Fetch recently-updated studies for each configured search term."""
    if config.OFFLINE:
        samples = json.loads(FIXTURE.read_text())
        events = []
        for term, payload in samples.items():
            events.extend(parse_studies(payload, term))
        return events

    events = []
    with httpx.Client(timeout=20) as client:
        for term in config.TRIAL_TERMS:
            resp = client.get(
                API_URL,
                params={
                    "query.term": term,
                    "pageSize": page_size,
                    "sort": "LastUpdatePostDate:desc",
                },
                headers={"User-Agent": config.USER_AGENT},
            )
            resp.raise_for_status()
            events.extend(parse_studies(resp.json(), term))
    return events
