"""FastAPI app serving the dashboard and a small JSON API.

Run with:
    uvicorn pulseboard.app:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from pulseboard import config, store

app = FastAPI(title="Pulseboard", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _db():
    return store.connect(config.DB_PATH)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = _db()
    ctx = {
        "counts": store.counts(conn),
        "feed": store.latest(conn, limit=30),
        "filings": store.latest(conn, source="edgar", limit=12),
        "trials": store.latest(conn, source="trials", limit=12),
        "news": store.latest(conn, source="news", limit=12),
        "offline": config.OFFLINE,
        "watchlist": config.WATCHLIST,
    }
    conn.close()
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/api/events")
def api_events(source: str | None = None, limit: int = 50):
    conn = _db()
    events = store.latest(conn, source=source, limit=min(limit, 200))
    conn.close()
    return {"count": len(events), "events": events}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}
