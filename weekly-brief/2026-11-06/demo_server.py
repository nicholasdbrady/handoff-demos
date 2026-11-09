# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv>=1.0,<2"]
# ///
"""Local presentation adapter. Only fixed, explicitly enabled demo commands run."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env", override=False)
SLUGS = frozenset({"azd-agent", "fal-video", "kimi-k3-1-pro", "kimi-k3-1-pro-benchmark", "maf-skills"})
ENDPOINTS = {
    "azd-agent": "AZD_AGENT_PROJECT_ENDPOINT", "maf-skills": "FOUNDRY_PROJECT_ENDPOINT",
    "kimi-k3-1-pro": "KIMI_ENDPOINT", "fal-video": "FOUNDRY_RESOURCE_ENDPOINT",
    "kimi-k3-1-pro-benchmark": "KIMI_ENDPOINT",
}
RUN_OPTIONS = {
    "kimi-k3-1-pro": ["--mode", "scene", "--effort", "none", "--max-tokens", "12000"],
    "kimi-k3-1-pro-benchmark": ["--trial", "1", "--effort", "high", "--max-tokens", "4096"],
}
ORIGINS = frozenset({"http://127.0.0.1:3080", "http://localhost:3080"})
TIMEOUT = 350
OUTPUT_LIMIT = 1_000_000
RUN_LOCK = threading.Lock()


class DemoError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def run_demo(slug: str) -> dict:
    if slug not in SLUGS:
        raise DemoError(404, "Unknown demo.")
    if os.environ.get("SLIDEV_ENABLE_LIVE") != "1":
        raise DemoError(409, "Live mode is disabled. Set SLIDEV_ENABLE_LIVE=1 and restart the adapter.")
    name = ENDPOINTS[slug]
    endpoint = os.environ.get(name, "").strip()
    if endpoint:
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise DemoError(400, f"{name} must be an HTTPS URL without credentials, query, or fragment.")
    manifest_path = HERE / "public" / "demos" / slug / "manifest.json"
    if not manifest_path.is_file():
        raise DemoError(409, "This demo has no capture manifest yet.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as error:
        raise DemoError(502, f"The demo manifest cannot be read: {error}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("live"), dict):
        raise DemoError(502, "The demo manifest has an invalid live configuration.")
    if manifest["live"].get("supported") is not True:
        raise DemoError(409, "This demo does not support live execution in this environment.")
    script = HERE / "demos" / slug / "run.py"
    if not script.is_file():
        raise DemoError(409, "The demo runner has not landed yet.")
    if not RUN_LOCK.acquire(blocking=False):
        raise DemoError(409, "Another demo is running. Wait for it to finish.")
    try:
        # File-backed output prevents an unbounded subprocess pipe from exhausting memory.
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = subprocess.Popen(
                ["uv", "run", str(script), "--json", *RUN_OPTIONS.get(slug, [])], cwd=HERE,
                stdout=stdout, stderr=stderr,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                start_new_session=os.name != "nt",
            )
            try:
                process.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired as error:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, check=False)
                else:
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise DemoError(504, f"Live execution exceeded {TIMEOUT} seconds; the runner was stopped.") from error
            stdout.seek(0)
            stderr.seek(0)
            output = stdout.read(OUTPUT_LIMIT + 1)
            diagnostic = stderr.read(16_000).decode("utf-8", errors="replace").strip()
            if process.returncode:
                failure = output[:16_000].decode("utf-8", errors="replace").strip()
                try:
                    error_result = json.loads(failure)
                except ValueError:
                    error_result = None
                if isinstance(error_result, dict) and isinstance(error_result.get("error"), str):
                    failure = error_result["error"]
                    prefix = f"Live run failed ({failure}): "
                    runner_detail = next((line for line in diagnostic.splitlines() if line.startswith(prefix)), "")
                    if runner_detail:
                        failure = runner_detail
                raise DemoError(502, f"Runner exited {process.returncode}. {failure or diagnostic}")
            if len(output) > OUTPUT_LIMIT:
                raise DemoError(502, "Runner output exceeded the JSON size limit.")
            try:
                result = json.loads(output.decode("utf-8-sig"))
            except (ValueError, UnicodeError) as error:
                raise DemoError(502, f"Runner did not emit one JSON object. {diagnostic}") from error
            if not isinstance(result, dict):
                raise DemoError(502, "Runner output must be one JSON object.")
            return {"mode": "live", "slug": slug, "result": result}
    except OSError as error:
        raise DemoError(503, f"The runner could not start: {error}") from error
    finally:
        RUN_LOCK.release()


class Handler(BaseHTTPRequestHandler):
    def respond(self, status: int, body: dict) -> None:
        payload = json.dumps(body, ensure_ascii=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def allowed(self) -> bool:
        host = self.headers.get("Host", "").split(":")[0]
        return (
            host in {"localhost", "127.0.0.1"}
            and self.headers.get("Origin") in ORIGINS | {None}
            and self.headers.get("X-Demo-Client") == "slidev"
        )

    def do_GET(self) -> None:
        if not self.allowed():
            self.respond(403, {"detail": "Use the local Slidev presentation."})
        elif self.path == "/demo-api/health":
            self.respond(200, {"status": "ready", "live_enabled": os.environ.get("SLIDEV_ENABLE_LIVE") == "1"})
        else:
            self.respond(404, {"detail": "Unknown route."})

    def do_POST(self) -> None:
        if not self.allowed():
            self.respond(403, {"detail": "Use the local Slidev presentation."})
            return
        path = urlsplit(self.path)
        slug = path.path.removeprefix("/demo-api/run/")
        if path.query or path.path != f"/demo-api/run/{slug}" or slug not in SLUGS:
            self.respond(404, {"detail": "Unknown demo route."})
            return
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            self.respond(400, {"detail": "This route takes no request body or custom command."})
            return
        try:
            self.respond(200, run_demo(slug))
        except DemoError as error:
            self.respond(error.status, {"detail": str(error), "mode": "live", "slug": slug})

    def log_message(self, format: str, *args) -> None:
        print(f"demo-adapter: {format % args}", flush=True)


class DemoServer(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main() -> None:
    server = DemoServer(("127.0.0.1", 8780), Handler)
    print("Demo adapter listening at http://127.0.0.1:8780", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
