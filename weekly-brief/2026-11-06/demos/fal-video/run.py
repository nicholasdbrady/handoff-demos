# /// script
# requires-python = ">=3.12"
# dependencies = ["azure-identity>=1.25,<2", "httpx>=0.28,<1", "python-dotenv>=1.1,<2"]
# ///
"""Submit one real fal-on-Foundry video; never substitute a recording."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import quote, urlparse

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
STATE: dict = {"request_id": None}
PROMPT = (
    "A calm developer workspace at dawn, an empty desk with an unbranded laptop "
    "showing abstract colored code blocks, a plain notebook and a warm cup of tea. "
    "Soft amber light, gentle steam, a slow smooth camera push forward, one continuous "
    "shot. A quiet transition from an idea to a working prototype. No people, "
    "faces, readable text, logos, or brands."
)
# Routes follow Microsoft Learn's versioned submit/retrieve examples.
# Dict order is the default preference: the live-verified, lowest-rate option first.
MODELS = {
    "minimax-h3-max-turbo": ("minimax/h3-max-turbo", "text-to-video", 5, "480P"),
    "ltx-2.5-fast": ("lightricks/ltx-2.5", "text-to-video/fast", 6, "720p"),
    "ltx-2.5-pro": ("lightricks/ltx-2.5", "text-to-video/pro", 6, "720p"),
    "minimax-h3-max": ("minimax/h3-max", "text-to-video", 5, "480P"),
    "kling-v3-pro": ("kling/v3/pro", "text-to-video", 5, None),
}


def object_env(name: str) -> dict:
    """Read a required JSON object without a silent configuration fallback."""
    value = json.loads(os.environ.get(name, "{}"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def check_endpoint(endpoint: str) -> str:
    """Restrict token delivery to the documented Azure resource endpoint."""
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".services.ai.azure.com")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("FOUNDRY_RESOURCE_ENDPOINT must be an HTTPS Azure resource root")
    return endpoint.rstrip("/")


def payload(model: str, deployment: str, prompt: str) -> dict:
    """Use the smallest documented text-to-video settings for the selected model."""
    _, _, duration, resolution = MODELS[model]
    body = {"model": deployment, "prompt": prompt, "duration": duration}
    if resolution:
        body["resolution"] = resolution
    if model.startswith("ltx"):
        body.update(aspect_ratio="16:9", fps=24, generate_audio=True)
    elif model.startswith("minimax"):
        body["prompt_expansion_mode"] = "disabled"
    else:
        body.update(duration=str(duration), aspect_ratio="16:9", generate_audio=False)
    return body


def probe(path: Path) -> dict:
    """Measure the downloaded file instead of reporting requested dimensions."""
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height,avg_frame_rate:format=duration",
            "-of", "json", str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(completed.stdout)
    streams = data["streams"]
    stream = next(s for s in streams if s.get("codec_type") == "video")
    numerator, denominator = map(float, stream["avg_frame_rate"].split("/"))
    width, height = int(stream["width"]), int(stream["height"])
    duration = float(data["format"]["duration"])
    if width <= 0 or height <= 0 or not math.isfinite(duration) or duration <= 0:
        raise ValueError("The downloaded file has invalid video metadata")
    return {
        "width": width, "height": height,
        "duration_s": duration, "fps": numerator / denominator,
        # Stream presence only; this does not assess what the audio sounds like.
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        "file_mb": round(path.stat().st_size / 1_000_000, 3),
    }


def generate(model: str, prompt: str, resume: str | None = None) -> dict:
    """Submit once (or resume a known request), poll, download, and measure a real clip."""
    if os.environ.get("FAL_ACCESS_CONFIRMED", "").lower() != "true":
        raise ValueError(
            "Live generation is unavailable: fal access has not been confirmed. "
            "An administrator must review terms and register Fal.EnableDeploy."
        )
    endpoint = check_endpoint(os.environ.get("FOUNDRY_RESOURCE_ENDPOINT", ""))
    deployments = object_env("FAL_DEPLOYMENTS")
    deployment = deployments.get(model)
    if not isinstance(deployment, str) or not deployment.strip():
        raise ValueError(f"No confirmed deployment configured for {model}")
    price = object_env("FAL_PRICES_PER_SECOND_USD").get(model)
    if (
        isinstance(price, bool) or not isinstance(price, (int, float))
        or not math.isfinite(price) or price <= 0
    ):
        raise ValueError(f"Confirm a positive USD/video-second price for {model} first")
    if not shutil.which("ffprobe"):
        raise ValueError("ffprobe is required to measure the generated video")
    if not prompt.strip():
        raise ValueError("Prompt must not be empty")
    if resume is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", resume):
        raise ValueError("request_id has an unexpected format")

    family, route, requested_duration, _ = MODELS[model]
    base = f"{endpoint}/providers/falai/v1/{family}"
    started = time.perf_counter()
    deadline = started + 900
    with DefaultAzureCredential() as credential, httpx.Client(timeout=60) as client:
        def request(method: str, url: str, **kwargs) -> dict:
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            response = client.request(
                method, url, headers={"Authorization": f"Bearer {token.token}"}, **kwargs
            )
            # Do not emit URLs, response bodies, or tokens in public JSON errors.
            if response.is_error:
                raise RuntimeError(f"Foundry {method} returned HTTP {response.status_code}")
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError("Foundry returned a non-object response")
            return result

        output = ROOT / "public" / "demos" / "fal-video" / "live"
        output.mkdir(parents=True, exist_ok=True)
        body = payload(model, deployment, prompt)
        if resume:
            request_id = resume
        else:
            submitted_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            submitted = request("POST", f"{base}/{route}", json=body)
            request_id = submitted.get("request_id")
            if not isinstance(request_id, str) or not request_id:
                raise ValueError("Foundry did not return a request_id; do not resubmit blindly")
            STATE["request_id"] = request_id
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
                raise ValueError("request_id has an unexpected format; do not resubmit blindly")
            # Persist immediately so a failed poll/download can resume without a second paid job.
            (output / f"{model}-{request_id}.request.json").write_text(json.dumps({
                "model": model, "deployment": deployment, "request_id": request_id,
                "route": f"/providers/falai/v1/{family}/{route}", "submitted_at": submitted_at,
                "payload": body,
            }, indent=2), encoding="utf-8")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            raise ValueError("request_id has an unexpected format")
        STATE["request_id"] = request_id
        result_url = f"{base}/requests/{quote(request_id, safe='')}"
        while True:
            if time.perf_counter() >= deadline:
                raise TimeoutError(
                    "Generation exceeded 900 seconds. The remote job may still run "
                    "and incur cost; inspect it before retrying."
                )
            status = request("GET", f"{result_url}/status").get("status")
            if status == "COMPLETED":
                break
            if status not in ("IN_QUEUE", "IN_PROGRESS"):
                raise RuntimeError(f"Generation ended with unexpected status {status!r}")
            time.sleep(5)
        result = request("GET", result_url)
        video = result.get("video")
        if not isinstance(video, dict) or not isinstance(video.get("url"), str):
            raise ValueError("Completed generation did not return a video URL")
        video_url = video["url"]
        if urlparse(video_url).scheme != "https":
            raise ValueError("Video download URL must use HTTPS")
        path = output / f"{model}-{request_id}.mp4"
        partial = path.with_suffix(".part")
        # Signed storage links do not receive the Azure bearer token.
        # Same-resource links can require it; never forward it across redirects.
        headers = {}
        if urlparse(video_url).hostname == urlparse(endpoint).hostname:
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        try:
            with client.stream("GET", video_url, headers=headers) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"Video download returned HTTP {response.status_code}")
                size = 0
                with partial.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 100_000_000:
                            raise ValueError("Video download exceeded 100 MB")
                        handle.write(chunk)
            if size == 0:
                raise ValueError("Video download was empty")
            metadata = probe(partial)
            partial.replace(path)
        finally:
            partial.unlink(missing_ok=True)
    return {
        "ok": True, "model": model, "deployment": deployment, "request_id": request_id,
        "prompt": prompt,
        "seconds": round(time.perf_counter() - started, 3),
        "video_path": path.relative_to(ROOT).as_posix(), **metadata,
        # Estimate from requested generation length, not re-encoded playback length.
        "est_cost_usd": round(requested_duration * price, 6),
    }


def main() -> int:
    """Print exactly one JSON result and return a nonzero status on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON (also the default)")
    parser.add_argument("--model", choices=tuple(MODELS))
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--resume", metavar="REQUEST_ID",
                        help="Poll/download an already-submitted request; never resubmits (needs --model)")
    args = parser.parse_args()
    if args.resume and not args.model:
        parser.error("--resume requires --model")
    STATE["request_id"] = None
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    load_dotenv(ROOT / ".env", override=False)
    model = args.model
    try:
        if model is None:
            deployments = object_env("FAL_DEPLOYMENTS")
            # Preference order, not a measured latency ranking across models.
            model = next(
                (name for name in MODELS if isinstance(deployments.get(name), str)
                 and deployments[name].strip()), "minimax-h3-max-turbo"
            )
        result = generate(model, args.prompt, args.resume)
    except (ValueError, RuntimeError, TimeoutError, httpx.HTTPError, AzureError,
            subprocess.SubprocessError, OSError, KeyError, IndexError,
            ZeroDivisionError) as error:
        result = {
            "ok": False, "model": model, "request_id": STATE["request_id"], "prompt": args.prompt,
            "seconds": None, "video_path": None, "width": None, "height": None,
            "duration_s": None, "est_cost_usd": None,
            "error": (
                f"{type(error).__name__}: authentication or network request failed"
                if isinstance(error, (httpx.HTTPError, AzureError)) else str(error)
            ),
        }
        print(json.dumps(result))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
