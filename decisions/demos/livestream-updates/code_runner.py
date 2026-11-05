"""Run one Monaco slide snippet with a prepared Decisions client.

demo_server.py starts this file in a new isolated interpreter for each run:
``python -I code_runner.py <rehearsal|live>`` with the snippet on stdin.
Settings come from the server's environment. Live mode never falls back to
the synthetic client.
"""

from __future__ import annotations

import linecache
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILENAME = "<slide>"


def build_namespace(mode: str) -> dict[str, object]:
    """Return the globals for slide code: ``client`` and ``DEPLOYMENT``."""
    sys.path.insert(0, str(HERE.parent / "decisions-api"))
    import decisions_factory as decisions

    if mode == "live":
        if not decisions.ENDPOINT:
            raise RuntimeError("Set AZURE_OPENAI_ENDPOINT in the deck's .env.")
        client = decisions.get_decisions_client().with_options(timeout=60, max_retries=0)
    else:
        client = decisions.MockClient()
    return {"__name__": "__slide__", "client": client, "DEPLOYMENT": decisions.DECISIONS_DEPLOYMENT}


def describe(error: BaseException) -> str:
    """Return a short error that shows slide lines, not runner internals."""
    from azure.core.exceptions import ClientAuthenticationError
    from openai import APIConnectionError, APIStatusError

    if isinstance(error, ClientAuthenticationError):
        return "Microsoft authentication failed. Run az login for the tenant that owns the resource, then retry."
    if isinstance(error, APIStatusError):
        message = re.sub(r"https?://\S+", "[link removed]", str(getattr(error, "message", "")))[:400]
        return f"{type(error).__name__}: HTTP {error.status_code}. {message}"
    if isinstance(error, APIConnectionError):
        return "Azure OpenAI could not be reached. Check the network and endpoint."
    if isinstance(error, SyntaxError):
        return "".join(traceback.format_exception_only(error)).rstrip()
    frames = [frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == FILENAME]
    return ("".join(traceback.format_list(frames)) + "".join(traceback.format_exception_only(error))).rstrip()


def main() -> int:
    """Execute stdin as slide code and print a concise error on failure."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("rehearsal", "live"):
        print("Usage: python -I code_runner.py <rehearsal|live>", file=sys.stderr)
        return 2
    code = sys.stdin.read()
    linecache.cache[FILENAME] = (len(code), None, code.splitlines(keepends=True), FILENAME)
    try:
        namespace = build_namespace(mode)
        exec(compile(code, FILENAME, "exec"), namespace)
    except BaseException as error:  # noqa: BLE001 - report every slide failure, including SystemExit.
        sys.stdout.flush()
        print(describe(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
