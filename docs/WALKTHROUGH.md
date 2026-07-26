# Code walkthrough

A tour of how Pulseboard works, file by file — written so you can explain any
part of it in an interview without notes.

## The one idea that matters

Three very different APIs (EDGAR JSON, ClinicalTrials JSON, RSS XML) are
normalised into **one event shape** as early as possible:

```python
{"source", "ref", "company", "title", "detail", "date", "url"}
```

Everything downstream — storage, dedupe, the merged feed, the UI — only knows
this shape. Adding a fourth source means writing one `fetch()` that returns
these dicts, and nothing else changes. If you take away one architectural
point, take this one.

## File by file

### `pulseboard/config.py`
All the knobs: watchlist tickers, which SEC form types are interesting, trial
search terms, RSS feeds, news keywords. `OFFLINE` flips every source to
bundled fixture data — that flag is what makes the app demoable and testable
with no network.

### `pulseboard/sources/edgar.py`
Two-step dance: SEC's `company_tickers.json` maps tickers to CIK numbers,
then `data.sec.gov/submissions/CIK##########.json` lists recent filings per
company. Note the split between `fetch()` (does HTTP) and
`parse_submissions()` (pure function) — tests exercise the parser with a
fixture and never touch the network. SEC's data comes as parallel arrays
(`form[]`, `filingDate[]`...), hence the `zip`. Insider ownership forms (3/4/5)
are filtered out because they fire constantly and rarely matter.

### `pulseboard/sources/clinicaltrials.py`
The v2 API nests everything under `protocolSection.*Module`. The defensive
`.get({}, {})` chains are deliberate: study records are wildly inconsistent,
and a missing sponsor shouldn't crash a refresh. `ref` includes the
last-update date so a study that changes status shows up again as a new event
— that's a feature, the dashboard is about *changes*.

### `pulseboard/sources/news.py`
RSS 2.0 parsed with stdlib `xml.etree` — a whole dependency (feedparser)
wasn't worth it for `<item><title><link><pubDate>`. Items must match a
funding keyword ("raises", "series b", "acquisition"...) to be kept.
Feeds that 404 are skipped, not fatal.

### `pulseboard/store.py`
SQLite with one table. The interesting line is `UNIQUE(source, ref)` plus
`INSERT OR IGNORE`: that makes `refresh` **idempotent** — run it hourly on a
cron and you never get duplicates. `upsert_events` counts rows before/after
to report how many were genuinely new.

### `pulseboard/app.py` + `templates/index.html`
FastAPI serving one server-rendered page plus a JSON API (`/api/events`).
Deliberately no React: it's a read-only dashboard, so server-side Jinja2 is
less code, fewer moving parts, and instant first paint. If it ever needs
interactivity, `/api/events` is already there to build against.

### `scripts/refresh.py`
Orchestrates all three sources, each in its own try/except — one broken
source still lets the others land. Prints a per-source summary so a cron log
is actually readable.

## Interview Q&A you should be able to field

**Why SQLite and not Postgres?** Single-user read-heavy dashboard, one
writer, dataset in the thousands of rows. SQLite is zero-ops and ships in the
stdlib. Postgres becomes right when there are concurrent writers or multiple
app servers.

**Why is parsing split from fetching?** Testability (parsers are pure
functions run against fixtures) and honesty about failure modes — network
problems and malformed data are different bugs and get handled in different
places.

**What breaks first at scale?** The refresh is sequential; with hundreds of
watchlist names you'd want request pooling/async, and EDGAR rate-limits
(~10 req/s) would need respecting explicitly. The events table would want
pagination in the API before the UI ever notices.

**What did AI do vs you?** AI assisted heavily with the implementation
(pair-programming style); the project choice, watchlist, scope, and data-source
decisions were mine, and I've reviewed and can explain every file — this
document is part of how I made sure of that.
