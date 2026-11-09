"""
decisions_factory — Livestream demo for the Azure OpenAI Decisions API.

The Decisions API (`POST /openai/v1/decisions`, model `gpt-6-luna`) returns
calibrated probabilities instead of generated text. You ask typed questions:

  predicate  → probability (0-1) that a statement is true
  choice     → best choice + probability per choice + confidence
  score      → probability-weighted score over ordered levels + confidence

This script walks a support-operations scenario in short, self-contained
steps so each one fits a livestream segment:

  1. predicate   Is the customer asking for a refund?
  2. choice      Which department owns this ticket?
  3. score       How severe is the issue?
  4. batch       One ticket, many questions, one call  (the "triage pack")
  5. route       Thresholds + refusals → auto-action or human review
  6. image       Is this photo valid proof of delivery?
  7. cache       Shared policy prefix + prompt_cache_key → cached input tokens
  8. latency     Decisions vs Responses structured output for the same task

Run `--mock` to rehearse offline. Mock answers are synthetic but use the real
`openai.types.decision.Decision` model, so the rendering code is identical.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import mimetypes
import os
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from openai import OpenAI
from openai.types.decision import Decision

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# ── Configuration ──────────────────────────────────────────────────────

AGENT_NAME = "decisions-api-demo"
ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DECISIONS_DEPLOYMENT = os.environ.get("DECISIONS_DEPLOYMENT", "gpt-6-luna")
RESPONSES_DEPLOYMENT = os.environ.get("RESPONSES_DEPLOYMENT", DECISIONS_DEPLOYMENT)
DEMO_IMAGE = os.environ.get("DEMO_IMAGE", "")

# Tune these on labeled data. Pick them by the cost of a wrong auto-action.
AUTO_ACTION_PROBABILITY = 0.85
MIN_CONFIDENCE = 0.70

STEPS = ["predicate", "choice", "score", "batch", "route", "image", "cache", "latency"]

# ── Sample data ────────────────────────────────────────────────────────

TICKETS: dict[str, str] = {
    "T-1001": (
        "I was charged twice for my annual plan this morning. I only want one "
        "subscription. Please return the extra charge to my card."
    ),
    "T-1002": (
        "Since the 2.14 update, every export to PDF fails with error 0x80070005. "
        "Our whole finance team is blocked and month-end close is tomorrow."
    ),
    "T-1003": (
        "Can you tell me if the Pro plan includes SSO? We are comparing vendors "
        "and want to decide this week."
    ),
    "T-1004": (
        "Someone logged in to my account from another country and changed my "
        "email address. I did not do this. I can't get back in."
    ),
    "T-1005": "The new dark theme looks great, thanks team!",
}

DEPARTMENTS = [
    {"value": "billing", "description": "Charges, invoices, refunds, plan changes"},
    {"value": "technical", "description": "Bugs, errors, outages, product not working"},
    {"value": "security", "description": "Account compromise, suspicious access, data exposure"},
    {"value": "sales", "description": "Pre-purchase questions, pricing, plan features"},
    {"value": "other", "description": "None of the above, including general feedback"},
]

SEVERITY_LEVELS = [
    {"label": "none", "description": "No problem reported; feedback or a question"},
    {"label": "low", "description": "Minor inconvenience with a workaround"},
    {"label": "medium", "description": "One user blocked or money at stake"},
    {"label": "high", "description": "A team is blocked or a business deadline is at risk"},
    {"label": "critical", "description": "Security incident, data loss, or broad outage"},
]

TRIAGE_PACK: list[dict[str, Any]] = [
    {
        "name": "wants_refund",
        "type": "predicate",
        "instructions": "The customer asks for money back or the reversal of a charge.",
    },
    {
        "name": "department",
        "type": "choice",
        "instructions": "Pick the team that should own this ticket.",
        "choices": DEPARTMENTS,
    },
    {
        "name": "severity",
        "type": "score",
        "instructions": "Rate the business impact of the reported issue.",
        "levels": SEVERITY_LEVELS,
    },
    {
        "name": "angry",
        "type": "predicate",
        "instructions": "The customer is frustrated or angry.",
    },
    {
        "name": "security_risk",
        "type": "predicate",
        "instructions": "The ticket describes a possible account takeover or unauthorized access.",
    },
    {
        "name": "churn_risk",
        "type": "predicate",
        "instructions": "The customer is likely to cancel or not buy if this is handled badly.",
    },
]

REFUND_POLICY = """\
Contoso Cloud — Refund and Escalation Policy (v7)
1. Duplicate charges are refunded in full within 5 business days. No approval needed.
2. Annual plans can be refunded pro rata within 30 days of renewal.
3. Monthly plans are not refunded for partial months.
4. Refunds above $5,000 require finance approval.
5. Possible account takeover is a P1 security incident. Freeze the account first.
6. Never promise a refund for a third-party marketplace purchase.
7. Outages covered by the SLA earn service credits, not cash refunds.
8. A customer who cites a legal claim is routed to legal, not support.
"""
# Padding makes the shared prefix large enough to show cache hits clearly.
POLICY_PREFIX = REFUND_POLICY + "\n".join(
    f"Appendix {i}: Regional terms for market {i} follow the base policy above "
    f"without changes, except that tax is calculated by local rules for region {i}."
    for i in range(1, 121)
)

# ── Tracing ────────────────────────────────────────────────────────────


def _init_tracer():
    """Start OpenTelemetry tracing when the shared lib dependencies exist."""
    try:
        from lib.tracing import setup_tracing

        return setup_tracing(AGENT_NAME)
    except Exception as exc:  # tracing must never break a live demo
        print(f"(tracing disabled: {exc})")
        return None


tracer = None


@contextlib.contextmanager
def span(name: str, **attrs: Any) -> Iterator[None]:
    """Wrap a step in an OpenTelemetry span when tracing is on."""
    if tracer is None:
        yield
        return
    with tracer.start_as_current_span(name) as s:
        for k, v in attrs.items():
            s.set_attribute(k, v)
        yield


# ── Client ─────────────────────────────────────────────────────────────


def token_scope() -> str:
    """Foundry inference and project routes use the Foundry token audience."""
    return (
        "https://ai.azure.com/.default"
        if (urlparse(ENDPOINT).hostname or "").endswith(".services.ai.azure.com")
        else "https://cognitiveservices.azure.com/.default"
    )


def get_decisions_client() -> OpenAI:
    """Return an OpenAI client for the Azure OpenAI v1 endpoint.

    Uses the API key when set. Otherwise uses Microsoft Entra ID through
    DefaultAzureCredential (needs the Cognitive Services OpenAI User role).
    """
    if not ENDPOINT:
        sys.exit("Set AZURE_OPENAI_ENDPOINT (or run with --mock).")
    base_url = ENDPOINT.rstrip("/") + "/openai/v1/"
    if API_KEY:
        return OpenAI(base_url=base_url, api_key=API_KEY)

    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), token_scope()
    )
    return OpenAI(base_url=base_url, api_key=token_provider)


# ── Mock mode ──────────────────────────────────────────────────────────

_KEYWORDS = {
    "billing": ["charged", "charge", "refund", "invoice", "card"],
    "technical": ["error", "fails", "update", "export", "bug"],
    "security": ["logged in", "another country", "changed my email", "did not do this"],
    "sales": ["pro plan", "include", "comparing vendors", "pricing"],
}


def _text_of(input_: Any) -> str:
    if isinstance(input_, str):
        return input_
    parts = []
    for msg in input_:
        content = msg["content"]
        if isinstance(content, str):
            parts.append(content)
        else:
            parts.extend(p.get("text", "[image]") for p in content)
    return "\n".join(parts)


def _mock_answer(q: dict[str, Any], text: str, rng: random.Random) -> dict[str, Any]:
    t = text.lower()
    hits = {k: sum(w in t for w in ws) for k, ws in _KEYWORDS.items()}
    name = q.get("name")
    if "[image]" in t and q["type"] == "predicate":
        return {"type": "predicate", "name": name, "probability": round(rng.uniform(0.6, 0.95), 3)}
    if q["type"] == "predicate":
        i = q["instructions"].lower()
        p = 0.08
        if "money back" in i or "refund" in i:
            p = 0.95 if hits["billing"] else 0.04
        elif "account takeover" in i or "frozen" in i:
            p = 0.97 if hits["security"] else 0.02
        elif "frustrated" in i:
            p = 0.81 if (hits["technical"] or hits["security"]) else 0.12
        elif "cancel" in i:
            p = 0.64 if hits["technical"] or hits["security"] else 0.18
        elif "medical" in i:
            return {"type": "refusal", "name": name}
        return {"type": "predicate", "name": name, "probability": round(max(0.0, min(1.0, p + rng.uniform(-0.03, 0.03))), 3)}
    if q["type"] == "choice":
        values = [c["value"] for c in q["choices"]]
        best = max(hits, key=hits.get) if any(hits.values()) else values[-1]
        best = best if best in values else values[-1]
        top = 0.55 if best == "other" else rng.uniform(0.86, 0.97)
        rest = (1 - top) / (len(values) - 1)
        probs = [{"value": v, "probability": round(top if v == best else rest, 3)} for v in values]
        return {"type": "choice", "name": name, "choice": best, "confidence": round(top, 3), "probabilities": probs}
    levels = q["levels"]
    level = 0
    if "[image]" in t:
        level = len(levels) - 1
    elif hits["security"]:
        level = 4
    elif hits["technical"]:
        level = 3
    elif hits["billing"]:
        level = 2
    level = min(level, len(levels) - 1)
    probs = [0.03] * len(levels)
    probs[level] = 0.0
    probs[level] = 1 - sum(probs)
    weighted = sum(i * p for i, p in enumerate(probs))
    return {
        "type": "score",
        "name": name,
        "score": round(weighted, 3),
        "confidence": round(max(probs), 3),
        "probabilities": [
            {"value": i, "label": lv["label"], "probability": round(p, 3)} for i, (lv, p) in enumerate(zip(levels, probs))
        ],
    }


class MockDecisions:
    """Offline stand-in for `client.decisions` that returns real `Decision` objects."""

    def __init__(self) -> None:
        self._seen_cache_keys: set[str] = set()

    def create(self, *, input: Any, model: str, questions: list[dict[str, Any]], **kwargs: Any) -> Decision:
        text = _text_of(input)
        rng = random.Random(len(text))
        time.sleep(0.12 + 0.02 * len(questions) ** 0.5)
        input_tokens = max(20, len(text) // 4)
        cache_key = kwargs.get("prompt_cache_key")
        cached = int(input_tokens * 0.9) if cache_key and cache_key in self._seen_cache_keys else 0
        if cache_key:
            self._seen_cache_keys.add(cache_key)
        return Decision.model_validate(
            {
                "model": model,
                "answers": [_mock_answer(q, text, rng) for q in questions],
                "usage": {
                    "input_tokens": input_tokens,
                    "input_tokens_details": {"cached_tokens": cached, "cache_write_tokens": 0},
                    "output_tokens": 0,
                    "output_tokens_details": {"reasoning_tokens": 0},
                    "total_tokens": input_tokens,
                },
            }
        )


class MockResponses:
    """Offline stand-in for `client.responses` used by the latency step."""

    def create(self, **kwargs: Any) -> Any:
        time.sleep(random.uniform(1.4, 2.2))
        return type("R", (), {"output_text": '{"department":"technical"}'})()


class MockClient:
    """Minimal client with the two surfaces this demo uses."""

    def __init__(self) -> None:
        self.decisions = MockDecisions()
        self.responses = MockResponses()


# ── Rendering helpers ──────────────────────────────────────────────────


def header(title: str) -> None:
    """Print a step banner that reads well on a stream."""
    print("\n" + "═" * 72)
    print(f"  {title}")
    print("═" * 72)


def bar(p: float, width: int = 24) -> str:
    """Return a text probability bar."""
    filled = round(max(0.0, min(1.0, p)) * width)
    return "█" * filled + "·" * (width - filled)


def show_answer(answer: Any) -> None:
    """Print one answer by type. Always check `type` first: any answer can be a refusal."""
    label = answer.name or "(unnamed)"
    if answer.type == "refusal":
        print(f"  {label:<16} REFUSAL — the model declined this question; other answers still count")
    elif answer.type == "predicate":
        print(f"  {label:<16} p(true) = {answer.probability:5.3f}  {bar(answer.probability)}")
    elif answer.type == "choice":
        print(f"  {label:<16} choice  = {answer.choice!s:<10} confidence {answer.confidence:.3f}")
        for c in sorted(answer.probabilities, key=lambda c: -c.probability):
            print(f"  {'':<18}{c.value!s:<12}{c.probability:5.3f}  {bar(c.probability, 16)}")
    elif answer.type == "score":
        levels = {p.value: p.label for p in answer.probabilities}
        nearest = levels.get(round(answer.score), "?")
        print(
            f"  {label:<16} score   = {answer.score:4.2f} (≈ {nearest})  confidence {answer.confidence:.3f}"
        )
        for p in answer.probabilities:
            print(f"  {'':<18}{p.value}:{p.label:<10}{p.probability:5.3f}  {bar(p.probability, 16)}")


def show_usage(decision: Decision, elapsed: float) -> None:
    """Print usage and latency. Output tokens are always 0 for Decisions."""
    u = decision.usage
    cached = u.input_tokens_details.cached_tokens if u.input_tokens_details else 0
    print(
        f"  ⏱ {elapsed * 1000:6.0f} ms   input {u.input_tokens} tok (cached {cached})   output {u.output_tokens} tok"
    )


def decide(client: Any, input_: Any, questions: list[dict[str, Any]], **kwargs: Any) -> tuple[Decision, float]:
    """Call the Decisions API and return the result and elapsed seconds."""
    start = time.perf_counter()
    result = client.decisions.create(
        model=DECISIONS_DEPLOYMENT, input=input_, questions=questions, **kwargs
    )
    return result, time.perf_counter() - start


# ── Routing ────────────────────────────────────────────────────────────


def route(decision: Decision) -> str:
    """Turn triage-pack answers into an action. Low confidence goes to a human."""
    answers = {a.name: a for a in decision.answers}
    if any(a.type == "refusal" for a in decision.answers):
        return "HUMAN REVIEW — a question was refused"

    security = answers.get("security_risk")
    if security and security.probability >= AUTO_ACTION_PROBABILITY:
        return "PAGE SECURITY ON-CALL — freeze account (policy §5)"

    dept = answers.get("department")
    if dept is None or dept.confidence < MIN_CONFIDENCE or dept.choice == "other":
        return "HUMAN REVIEW — department unclear"

    refund = answers.get("wants_refund")
    severity = answers.get("severity")
    sev = f"severity {severity.score:.1f}" if severity else ""
    if refund and refund.probability >= AUTO_ACTION_PROBABILITY and dept.choice == "billing":
        return f"AUTO — open refund workflow in billing ({sev})"
    return f"AUTO — queue to {dept.choice} ({sev})"


# ── Steps ──────────────────────────────────────────────────────────────


def step_predicate(client: Any) -> None:
    """Predicate: one yes/no question returns a probability, not a label."""
    header("1 · PREDICATE — Is the customer asking for a refund?")
    q = [TRIAGE_PACK[0]]
    for tid in ("T-1001", "T-1003"):
        print(f"\n  {tid}: {TICKETS[tid]}")
        result, elapsed = decide(client, TICKETS[tid], q)
        show_answer(result.answers[0])
        show_usage(result, elapsed)


def step_choice(client: Any) -> None:
    """Choice: pick a category and get a probability for every option."""
    header("2 · CHOICE — Which department owns this ticket?")
    tid = "T-1004"
    print(f"\n  {tid}: {TICKETS[tid]}")
    result, elapsed = decide(client, TICKETS[tid], [TRIAGE_PACK[1]])
    show_answer(result.answers[0])
    show_usage(result, elapsed)


def step_score(client: Any) -> None:
    """Score: ordered levels return a weighted score that can fall between levels."""
    header("3 · SCORE — How severe is the issue?")
    tid = "T-1002"
    print(f"\n  {tid}: {TICKETS[tid]}")
    result, elapsed = decide(client, TICKETS[tid], [TRIAGE_PACK[2]])
    show_answer(result.answers[0])
    show_usage(result, elapsed)


def step_batch(client: Any) -> None:
    """Batch: six questions about one ticket in one call (up to 400 are allowed)."""
    header("4 · BATCH — The triage pack: 6 questions, 1 request")
    tid = "T-1004"
    print(f"\n  {tid}: {TICKETS[tid]}\n")
    result, elapsed = decide(client, TICKETS[tid], TRIAGE_PACK)
    for a in result.answers:
        show_answer(a)
    show_usage(result, elapsed)


def step_route(client: Any) -> None:
    """Route: run the triage pack over every ticket in parallel and apply thresholds."""
    header("5 · ROUTE — Thresholds and refusals decide auto-action vs human review")
    print(f"  auto-action if p ≥ {AUTO_ACTION_PROBABILITY}; human review if confidence < {MIN_CONFIDENCE}\n")
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(TICKETS)) as pool:
        results = dict(zip(TICKETS, pool.map(lambda t: decide(client, t, TRIAGE_PACK)[0], TICKETS.values())))
    total = time.perf_counter() - start
    for tid, result in results.items():
        print(f"  {tid}  {TICKETS[tid][:46]:<46}…  → {route(result)}")
    print(f"\n  {len(TICKETS)} tickets × {len(TRIAGE_PACK)} questions in {total * 1000:.0f} ms (parallel)")

    print("\n  Refusal handling — add a question the model may decline:")
    risky = TRIAGE_PACK + [
        {
            "name": "medical",
            "type": "predicate",
            "instructions": "Infer the customer's medical condition from the ticket.",
        }
    ]
    result, _ = decide(client, TICKETS["T-1002"], risky)
    show_answer(result.answers[-1])
    print(f"  route → {route(result)}")


def _image_part(source: str) -> dict[str, Any]:
    """Return an input_image part from a public URL or a local file (as a data URL)."""
    if source.startswith(("http://", "https://", "data:")):
        return {"type": "input_image", "image_url": source}
    path = Path(source)
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    return {"type": "input_image", "image_url": f"data:{mime};base64,{data}"}


def step_image(client: Any, image: str) -> None:
    """Image: decide over a photo — is this valid proof of delivery?"""
    header("6 · IMAGE — Is this photo valid proof of delivery?")
    if not image:
        if not isinstance(client, MockClient):
            print("  Skipped. Set DEMO_IMAGE or pass --image <path-or-url>.")
            return
        image = "https://example.com/mock-doorstep.jpg"
    print(f"  image: {image if len(image) < 80 else image[:77] + '...'}\n")
    input_ = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Driver photo submitted for order #48213 (residential address)."},
                _image_part(image),
            ],
        }
    ]
    questions = [
        {"name": "package_visible", "type": "predicate", "instructions": "A parcel or package is clearly visible."},
        {"name": "at_a_door", "type": "predicate", "instructions": "The package is at a building entrance or door."},
        {"name": "label_readable", "type": "predicate", "instructions": "A shipping label is visible and readable."},
        {
            "name": "photo_quality",
            "type": "score",
            "instructions": "Rate whether the photo is usable as delivery evidence.",
            "levels": [
                {"label": "unusable", "description": "Blurry, dark, or the subject is missing"},
                {"label": "weak", "description": "Subject visible but context is unclear"},
                {"label": "good", "description": "Package and location are both clear"},
            ],
        },
    ]
    result, elapsed = decide(client, input_, questions)
    for a in result.answers:
        show_answer(a)
    show_usage(result, elapsed)
    ok = all(a.type == "predicate" and a.probability >= 0.7 for a in result.answers[:2])
    print(f"\n  → {'ACCEPT proof of delivery' if ok else 'ASK DRIVER FOR A NEW PHOTO'}")


def step_cache(client: Any) -> None:
    """Cache: the input (not the questions) is cached. Put shared content first."""
    header("7 · CACHE — Shared policy prefix + prompt_cache_key")
    key = "contoso-refund-policy-v7"
    for i, tid in enumerate(("T-1001", "T-1004"), start=1):
        input_ = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": POLICY_PREFIX, "prompt_cache_breakpoint": {"mode": "explicit"}},
                    {"type": "input_text", "text": f"Ticket {tid}: {TICKETS[tid]}"},
                ],
            }
        ]
        questions = [
            {
                "name": "refund_allowed",
                "type": "predicate",
                "instructions": "Under the policy above, support may approve a refund without finance approval.",
            },
            {
                "name": "security_first",
                "type": "predicate",
                "instructions": "Under the policy above, the account must be frozen before anything else.",
            },
        ]
        result, elapsed = decide(client, input_, questions, prompt_cache_key=key)
        print(f"\n  call {i} ({'warm-up' if i == 1 else 'cache hit expected'}) — {tid}")
        for a in result.answers:
            show_answer(a)
        show_usage(result, elapsed)
    print("\n  Tip: send one warm-up call before a parallel burst so every worker hits the cache.")


def step_latency(client: Any, runs: int = 5) -> None:
    """Latency: same classification with Decisions vs Responses structured output."""
    header("8 · LATENCY — Decisions vs Responses structured output")
    ticket = TICKETS["T-1002"]
    choice_q = [TRIAGE_PACK[1]]
    schema = {
        "type": "json_schema",
        "name": "route",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"department": {"type": "string", "enum": [d["value"] for d in DEPARTMENTS]}},
            "required": ["department"],
            "additionalProperties": False,
        },
    }

    def time_decisions() -> float:
        return decide(client, ticket, choice_q)[1]

    def time_responses() -> float:
        start = time.perf_counter()
        client.responses.create(
            model=RESPONSES_DEPLOYMENT,
            input=f"Pick the department for this ticket.\n\n{ticket}",
            text={"format": schema},
        )
        return time.perf_counter() - start

    time_decisions()  # warm-up
    d = [time_decisions() for _ in range(runs)]
    r = [time_responses() for _ in range(runs)]
    md, mr = statistics.median(d) * 1000, statistics.median(r) * 1000
    print(f"\n  Decisions  median {md:7.0f} ms   (probabilities for every department)")
    print(f"  Responses  median {mr:7.0f} ms   (one JSON label, no calibrated confidence)")
    print(f"\n  → Decisions was {mr / md:.1f}× faster over {runs} runs")


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Parse arguments and run the selected demo steps."""
    global tracer
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--step", choices=["all", *STEPS], default="all", help="Run one step or all of them.")
    parser.add_argument("--mock", action="store_true", help="Rehearse offline with synthetic answers.")
    parser.add_argument("--image", default=DEMO_IMAGE, help="Local path or public URL for the image step.")
    parser.add_argument("--pause", action="store_true", help="Wait for Enter between steps (stream mode).")
    args = parser.parse_args()

    client: Any = MockClient() if args.mock else get_decisions_client()
    if not args.mock:
        tracer = _init_tracer()
    print(f"Decisions API demo · deployment={DECISIONS_DEPLOYMENT} · {'MOCK' if args.mock else ENDPOINT}")

    runners = {
        "predicate": lambda: step_predicate(client),
        "choice": lambda: step_choice(client),
        "score": lambda: step_score(client),
        "batch": lambda: step_batch(client),
        "route": lambda: step_route(client),
        "image": lambda: step_image(client, args.image),
        "cache": lambda: step_cache(client),
        "latency": lambda: step_latency(client),
    }
    selected = STEPS if args.step == "all" else [args.step]
    for i, name in enumerate(selected):
        with span(f"decisions.{name}", deployment=DECISIONS_DEPLOYMENT):
            runners[name]()
        if args.pause and i < len(selected) - 1:
            input("\n  [Enter] next step › ")


if __name__ == "__main__":
    main()
