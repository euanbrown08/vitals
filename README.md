# Pulseboard

A small healthtech market-intelligence dashboard. It pulls three public data
streams into one SQLite-backed "catalyst feed" for a watchlist of digital
health companies:

* **SEC EDGAR** — recent filings (8-K, 10-Q, 10-K, S-1...) for each watchlist ticker
* **ClinicalTrials.gov** — recently updated studies for tracked topics (digital
  therapeutics, remote monitoring, AI diagnosis)
* **Funding news** — keyword-filtered items from healthtech RSS feeds

I built it because following early-stage healthtech means watching three
different websites that never talk to each other. Now it's one page.

## Run it

```bash
pip install -r requirements.txt

# tell SEC who you are (they ask API users to identify themselves)
export PULSEBOARD_CONTACT="you@example.com"

python -m scripts.refresh          # pull live data into pulseboard.db
uvicorn pulseboard.app:app         # serve the dashboard on :8000
```

No API keys needed — all three sources are public.

Offline demo (bundled sample data, no network):

```bash
PULSEBOARD_OFFLINE=1 python -m scripts.refresh
PULSEBOARD_OFFLINE=1 uvicorn pulseboard.app:app
```

## Tests

```bash
python -m pytest
```

Parsing is separated from fetching, so the test suite runs entirely offline
against fixtures in `tests/fixtures/`.

## Design notes

* One normalised event shape across all sources, so merging into a single
  feed is trivial (see `pulseboard/store.py`).
* Sources fail independently — a dead RSS feed doesn't kill a refresh.
* Dedupe happens in SQLite (`UNIQUE(source, ref)`), so refreshes are
  idempotent and cheap to run on a schedule.
* No frontend framework: server-rendered Jinja2 + a little CSS. For a
  read-only dashboard that's simpler to run and easier to reason about.

See [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) for a guided tour of the code.

## Roadmap

- [ ] Price/volume context for watchlist tickers
- [ ] Email/Slack digest of new catalysts
- [ ] Per-company pages joining filings + trials + news

## Credits

Built by Euan, developed with AI pair-programming assistance; architecture,
scope and every line reviewed and owned by me. Data courtesy of SEC EDGAR and
ClinicalTrials.gov public APIs.
