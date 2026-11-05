# Decisions API demo

This demo shows the **Azure OpenAI Decisions API** (`POST /openai/v1/decisions`).
The API returns calibrated probabilities, not generated text. Use it when your code
needs to branch on an answer: route, filter, gate, or escalate.

Docs: [Use the Decisions API](https://learn.microsoft.com/azure/foundry/openai/how-to/decisions?tabs=python)

## What it shows

| Step | Question type | Scenario | Key point |
|---|---|---|---|
| `predicate` | predicate | Does the customer ask for a refund? | You get `probability`, not "yes". |
| `choice` | choice | Which department owns the ticket? | You get a probability for **every** option, plus `confidence`. |
| `score` | score | How severe is the issue? | `score` is a weighted average. It can fall between levels (for example 2.85). |
| `batch` | all three | 6-question triage pack, 1 call | Up to 400 questions per request. One input, many decisions. |
| `route` | all three | 5 tickets in parallel + thresholds | Your thresholds turn probabilities into actions. Refusals and low confidence go to a human. |
| `image` | predicate + score | Is the photo valid proof of delivery? | Images in the input (URL or base64 data URL). |
| `cache` | predicate | Shared policy prefix | `prompt_cache_key` + `prompt_cache_breakpoint`. The **input** is cached, not the questions. |
| `latency` | choice | Decisions vs Responses structured output | Same task, measured live. Decisions is the low-latency path. |

## Facts to say on stream

- **Model:** `gpt-6-luna` only. Pass your deployment name as `model`.
- **Regions:** rolling out to gpt-6-luna regions. East US 2 is not supported yet.
- **Endpoint:** the v1 endpoint, `https://<resource>.openai.azure.com/openai/v1/`. Use the standard `OpenAI` client.
- **Auth:** API key or Microsoft Entra ID (scope `https://cognitiveservices.azure.com/.default`).
- **SDK:** `openai>=3.26.0` → `client.decisions.create(model, input, questions)`.
- **Limits:** up to 400 questions and 128 images (32 MB) per request. Question names must be unique.
- **No output tokens.** `usage.output_tokens` is always 0.
- **Refusals are per question.** Any answer can be `type: "refusal"`. Check `type` before you read a value.
- **Dependent questions need separate calls.** All questions in a request see the same input. They don't see each other's answers.
- **Thresholds are yours.** Tune them on labeled data by the cost of a false positive versus a false negative.
- **When not to use it:** if you need generated text, JSON objects, or tool calls, use the Responses API or structured outputs.

## Setup

1. Deploy `gpt-6-luna` in a supported region.
2. Copy `.env.example` to `.env` and set `AZURE_OPENAI_ENDPOINT`.
   Leave `AZURE_OPENAI_API_KEY` empty to use Entra ID. Your identity then needs the
   **Cognitive Services OpenAI User** role.
3. Optional: set `DEMO_IMAGE` to a delivery photo (a local file or a public HTTPS URL).

## Run

From the repository root:

```powershell
# Rehearse offline. No Azure calls. Synthetic answers, same rendering.
uv run --with-requirements demos\decisions-api\requirements.txt python demos\decisions-api\decisions_factory.py --mock

# Live, all steps, pause between steps for the stream
uv run --with-requirements demos\decisions-api\requirements.txt python demos\decisions-api\decisions_factory.py --pause

# Live, one step
uv run --with-requirements demos\decisions-api\requirements.txt python demos\decisions-api\decisions_factory.py --step image --image .\doorstep.jpg
```

> On Windows terminals, set `$env:PYTHONIOENCODING='utf-8'` if the bar characters do not render.

## Core code (show this on screen)

```python
from openai import OpenAI

client = OpenAI(base_url=f"{endpoint}/openai/v1/", api_key=api_key)

decision = client.decisions.create(
    model="gpt-6-luna",
    input="Someone logged in from another country and changed my email.",
    questions=[
        {"name": "security_risk", "type": "predicate",
         "instructions": "The ticket describes a possible account takeover."},
        {"name": "department", "type": "choice",
         "instructions": "Pick the team that should own this ticket.",
         "choices": [{"value": "billing"}, {"value": "security"}, {"value": "other"}]},
    ],
)

for answer in decision.answers:
    if answer.type == "refusal":
        send_to_human(answer.name)
    elif answer.type == "predicate" and answer.probability >= 0.85:
        page_security_on_call()
```

## Talk track (about 12 minutes)

1. **Hook (1 min).** "Most LLM calls in production are not chat. They are decisions: is this spam, which queue, how urgent. Today you can ask for those as probabilities."
2. **`predicate` (1 min).** Two tickets. 0.97 versus 0.02. Point out: no parsing, no "yes/no" string matching.
3. **`choice` (1 min).** Show the full distribution. "You know how sure the model is, and what the runner-up is."
4. **`score` (1 min).** Point at the fractional score. "It's an expected value, not a bucket."
5. **`batch` (2 min).** Six questions, one call. "You can send up to 400."
6. **`route` (2 min).** This is the money slide. Probabilities + your thresholds = actions. Show the refusal going to human review.
7. **`image` (1 min).** Proof of delivery. Same API, image input.
8. **`cache` (1 min).** Cached tokens on call 2. "Put the shared content first. The input is cached, not the questions."
9. **`latency` (2 min).** Run it live. Let the numbers speak.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `404` on `/decisions` | The deployment is not `gpt-6-luna`, or the region does not have Decisions yet. |
| `AttributeError: 'OpenAI' object has no attribute 'decisions'` | Upgrade: `openai>=3.26.0`. |
| `401` with Entra ID | Assign **Cognitive Services OpenAI User** on the resource. Wait a few minutes. |
| `400` duplicate question name | Every `name` in a request must be unique. |
| Image step skipped | Set `DEMO_IMAGE` or pass `--image`. |
| Cached tokens are 0 | The shared prefix is too short, or the first call has not finished. Send the warm-up call first. |
