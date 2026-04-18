from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator, Iterator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .api.routes.simulation import router as simulation_router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
BACKEND_DIR = Path(__file__).resolve().parents[1]
WATCHED_SUFFIXES = {".html", ".css", ".js", ".py"}
LIVE_RELOAD_SNIPPET = """
<script>
  (() => {
    const protocol = window.location.protocol === "https:" ? "https" : "http";
    const streamUrl = `${protocol}://${window.location.host}/dev/events`;
    let source;

    function connect() {
      source = new EventSource(streamUrl);
      source.addEventListener("reload", () => window.location.reload());
      source.onerror = () => {
        source.close();
        window.setTimeout(connect, 800);
      };
    }

    connect();
  })();
</script>
""".strip()

app = FastAPI(
    title="EKG Simulator API",
    version="0.1.0",
    description=(
        "API para simular ECG vetorial, aplicar vetor de injúria no segmento ST "
        "e retornar projeções/dano segmentar para um app web."
    ),
)

app.include_router(simulation_router)
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dev")


def iter_watched_files() -> Iterator[Path]:
    for base_dir in (FRONTEND_DIR, BACKEND_DIR):
        for path in base_dir.rglob("*"):
            if path.is_file() and path.suffix in WATCHED_SUFFIXES:
                yield path


def compute_snapshot() -> tuple[tuple[str, int], ...]:
    snapshot = []
    for path in iter_watched_files():
        stat = path.stat()
        snapshot.append((str(path.relative_to(FRONTEND_DIR.parent)), stat.st_mtime_ns))
    snapshot.sort()
    return tuple(snapshot)


@app.get("/dev", response_class=HTMLResponse)
def dev_index() -> HTMLResponse:
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    injected_html = html.replace("</body>", f"{LIVE_RELOAD_SNIPPET}\n  </body>")
    return HTMLResponse(
        content=injected_html,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/dev/electrode-editor", response_class=HTMLResponse)
def dev_electrode_editor() -> HTMLResponse:
    html = (FRONTEND_DIR / "electrode-editor.html").read_text(encoding="utf-8")
    injected_html = html.replace("</body>", f"{LIVE_RELOAD_SNIPPET}\n  </body>")
    return HTMLResponse(
        content=injected_html,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/dev/events")
async def dev_events() -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        previous_snapshot = compute_snapshot()
        while True:
            await asyncio.sleep(0.8)
            current_snapshot = compute_snapshot()
            if current_snapshot != previous_snapshot:
                previous_snapshot = current_snapshot
                yield "event: reload\ndata: updated\n\n"
            else:
                yield "event: ping\ndata: ok\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
        },
    )
