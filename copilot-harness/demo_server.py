"""Loopback-only Slidev bridge; token renewal never occurs on the request path."""

from __future__ import annotations

import logging
import asyncio
import os
import threading
import time
import json
from contextlib import asynccontextmanager
from pathlib import Path
from queue import Queue
from typing import Any, Literal
from urllib.parse import quote

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from openai import APIError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from copilot_harness_factory import AGENTS, stream_agent, shared_task, get_project_client

LOG = logging.getLogger(__name__)
READY = threading.Event()
STOP = threading.Event()
TOKEN: dict[str, Any] = {}
LOCK = threading.Lock()
FILES: dict[str, dict[str, str]] = {lane: {} for lane in AGENTS}
PROJECT = None
HOSTED = None
MODEL_LOCK = threading.Lock()


def renew_token() -> None:
    """Fetch and refresh Entra credentials in a worker, with explicit failure state."""
    with DefaultAzureCredential() as credential:
        while not STOP.is_set():
            try:
                token = credential.get_token("https://ai.azure.com/.default")
                with LOCK:
                    TOKEN.update(value=token.token, expires=token.expires_on)
                READY.set()
                STOP.wait(max(30, token.expires_on - time.time() - 300))
            except AzureError:
                READY.clear()
                LOG.exception("Entra token refresh failed; live actions are disabled.")
                STOP.wait(30)


def cached_token() -> str:
    """Return only an already valid token; never sign in from a measured request."""
    with LOCK:
        if not READY.is_set() or TOKEN.get("expires", 0) <= time.time() + 30:
            raise RuntimeError("Entra token is not ready. Wait for background renewal.")
        return TOKEN["value"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Own the project client and credential renewal worker."""
    global PROJECT, HOSTED
    STOP.clear()
    PROJECT = get_project_client(allow_preview=True) if os.environ.get("SLIDEV_ENABLE_LIVE") == "1" else None
    worker = None
    if PROJECT is not None and os.environ.get("SLIDEV_ENABLE_LIVE") == "1":
        worker = threading.Thread(target=renew_token, daemon=True)
        worker.start()
        if (Path(__file__).parent / "hosted" / "lane_runner.py").is_file():
            from hosted import lane_runner
            await asyncio.to_thread(lane_runner.warmup)
            HOSTED = lane_runner
    yield
    STOP.set()
    if worker:
        worker.join(timeout=3)
    if PROJECT is not None:
        PROJECT.close()
    if HOSTED is not None:
        await asyncio.to_thread(HOSTED.shutdown)
        HOSTED = None
    READY.clear()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])


@app.middleware("http")
async def local_only(request: Request, call_next: Any) -> Response:
    """Reject cross-origin requests and protect actions with a custom client header."""
    if request.headers.get("origin") not in (None, "http://127.0.0.1:3070", "http://localhost:3070"):
        return Response("Use the local presentation.", status_code=403)
    download = request.method == "GET" and request.url.path.startswith("/demo-api/files/")
    if request.headers.get("X-Demo-Client") != "slidev" and not download:
        return Response("Use the local presentation.", status_code=403)
    if download and request.headers.get("sec-fetch-site") not in (None, "same-origin", "same-site", "none"):
        return Response("Cross-site downloads are not allowed.", status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/demo-api/status")
def status() -> dict[str, Any]:
    """Expose readiness, never credentials or authentication diagnostics."""
    enabled = os.environ.get("SLIDEV_ENABLE_LIVE") == "1"
    ready = enabled and PROJECT is not None and READY.is_set()
    return {"ready": ready, "model_running": MODEL_LOCK.locked(),
            "hosted": HOSTED.get_live_lanes() if HOSTED else None,
            "message": "Live ready." if ready else "Live disabled or background sign-in pending; recorded mode available."}


class CachedProject:
    """Inject the background-renewed token into the shared SDK client."""

    def get_openai_client(self, **kwargs: Any) -> Any:
        """Create an agent-scoped client that cannot trigger credential refresh."""
        return PROJECT.get_openai_client(api_key=cached_token, **kwargs)


def ndjson(events: Any) -> Any:
    """Preserve failures as explicit stream events; never synthesize success."""
    try:
        for event in events:
            yield json.dumps(public_event(event)) + "\n"
    except (APIError, AzureError, RuntimeError, ValueError, OSError) as error:
        LOG.exception("Live Responses stream failed")
        yield json.dumps({"type": "error", "message": str(error)}) + "\n"
    finally:
        MODEL_LOCK.release()


def public_event(value: Any) -> Any:
    """Expose supported summaries, never encrypted or raw reasoning content."""
    if isinstance(value, list):
        return [public_event(item) for item in value]
    if isinstance(value, dict):
        return {key: public_event(item) for key, item in value.items()
                if key != "encrypted_content" and not (value.get("type") == "reasoning" and key == "content")}
    return value


def archive_result(lane: str, result: dict[str, Any]) -> None:
    """Archive live evidence privately without replacing the selected replay."""
    directory = Path(__file__).parent / ".logs" / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{lane}-{time.time_ns()}.json").write_text(
        json.dumps(public_event(result), indent=2), encoding="utf-8")


def live_response(events: Any) -> StreamingResponse:
    """Finish and archive the owned model run even if a browser disconnects."""
    messages: Queue[str | None] = Queue()

    def produce() -> None:
        try:
            for line in ndjson(events):
                messages.put(line)
        finally:
            messages.put(None)

    async def consume():
        while True:
            line = await asyncio.to_thread(messages.get)
            if line is None:
                return
            yield line

    threading.Thread(target=produce, name="live-model-lane", daemon=True).start()
    return StreamingResponse(consume(), media_type="application/x-ndjson",
                             headers={"X-Accel-Buffering": "no"})


@app.post("/demo-api/stream/{lane}")
def stream_run(lane: Literal["default", "copilot", "probe"]) -> StreamingResponse:
    """Stream real model deltas and tool events directly to the slide."""
    if not status()["ready"]:
        raise HTTPException(503, "Live calls are disabled or background authentication is not ready.")
    if not MODEL_LOCK.acquire(blocking=False):
        raise HTTPException(409, "Another live lane is running. Calls are serialized for the deployment quota.")
    agent_lane = "copilot" if lane == "probe" else lane
    query = "What can you help me do? Reply in at most five short lines." if lane == "probe" else shared_task()

    def events():
        captured = []
        for event in stream_agent(CachedProject(), agent_lane, query):
            if event["type"] == "result":
                event["result"]["stream_events"] = captured
                FILES[agent_lane].update({file["id"]: file["name"] for file in event["result"]["files"]})
                if lane != "probe":
                    try:
                        archive_result(agent_lane, event["result"])
                    except OSError:
                        LOG.exception("The live run completed, but its evidence archive could not be saved")
                        yield {"type": "step", "name": "recording_error",
                               "detail": "Live run completed; evidence archive failed. Check adapter logs."}
            else:
                captured.append(public_event(event))
            yield event
    return live_response(events())


@app.post("/demo-api/stream/hosted/{lane}")
def stream_hosted(lane: Literal["sdk", "maf"]) -> StreamingResponse:
    """Mount the sibling's real hosted Responses stream without browser tokens."""
    if not status()["ready"]:
        raise HTTPException(503, "Live calls are disabled or authentication is pending.")
    if HOSTED is None or not HOSTED.get_live_lanes()["credentials_ready"]:
        raise HTTPException(503, "The hosted streaming adapter is not ready. Check startup and background authentication.")
    if not MODEL_LOCK.acquire(blocking=False):
        raise HTTPException(409, "Another live lane is running. Calls are serialized.")
    def events():
        captured = []
        for event in HOSTED.stream_lane(lane):
            if event["type"] == "step":
                event = {**event, "detail": event.get("detail") or event.get("text", "")}
            if event["type"] == "result":
                event["result"]["mode"] = "live"
                event["result"]["stream_events"] = captured
                try:
                    archive_result(f"hosted-{lane}", event["result"])
                except OSError:
                    LOG.exception("Hosted live run completed, but its recording could not be saved")
                    yield {"type": "step", "name": "recording_error",
                           "detail": "Live run completed; recording could not be saved. Check adapter logs."}
            else:
                captured.append(public_event(event))
            yield event
    return live_response(events())


@app.get("/demo-api/files/{lane}/{file_id}")
def download(lane: Literal["default", "copilot"], file_id: str) -> Response:
    """Download only file IDs observed in a response from this local session."""
    if file_id not in FILES[lane]:
        raise HTTPException(404, "This file was not returned by a live run in this session.")
    try:
        with CachedProject().get_openai_client() as client:
            content = client.files.content(file_id).read()
        return Response(content, media_type="application/octet-stream",
                        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(FILES[lane][file_id], safe='')}"})
    except (APIError, AzureError, RuntimeError) as error:
        LOG.exception("Generated file download failed")
        raise HTTPException(502, "Generated-file download failed. Check project-scoped agent permissions.") from error


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3071, log_level="info")
