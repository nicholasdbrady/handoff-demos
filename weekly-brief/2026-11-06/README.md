# The Handoff: weekly Foundry news brief

25-slide developer briefing for November 9, 2026. Reporting window:
October 30 13:01 PDT through November 6 12:01 PST.

You need Node.js 22.12 or later and npm. Python 3.11+ and
[uv](https://docs.astral.sh/uv/) are needed for the optional adapter; individual
demos can require a newer Python version, Azure CLI, or azd 1.37+.
The azd invocation needs Python 3.13+; Kimi needs Python 3.12+; the Agent
Framework and fal runners need Python 3.11+. uv can install those runtimes.

```powershell
git clone --branch nicholasdbrady-weekly-brief-nov-9 https://github.com/nicholasdbrady/handoff-demos.git
Set-Location handoff-demos\weekly-brief\2026-11-06
npm ci --registry=https://packagefeedproxy.microsoft.io/npm/
Copy-Item .env.example .env
npm run dev
```

Open http://127.0.0.1:3080 or http://127.0.0.1:3080/presenter for notes.
The static explanations need no cloud access. Demo panels read their own
`public/demos/<slug>/manifest.json`. Missing evidence is explicitly pending;
unavailable and partial demonstrations keep their caveats. Assets are real
captures or explicitly labeled educational source material, not fabricated runs.

For the local live-command adapter:

```powershell
# Edit .env: enable live only after configuring each demo's prerequisites.
uv run --index-url https://packagefeedproxy.microsoft.io/pypi/simple demo_server.py
```

The adapter listens only on http://127.0.0.1:8780. Live controls require a
manifest with `live.supported: true`, an enabled adapter, and a fixed runner
at `demos/<slug>/run.py`. They run `uv run demos/<slug>/run.py --json` with a
350-second timeout. The Kimi button adds fixed `--mode scene --effort none
--max-tokens 12000` arguments; use its README commands to test other settings.
The benchmark button runs trial 1 at high effort with a 4,096-token completion
cap. Before a live benchmark, follow
[its corpus rebuild steps](demos/kimi-k3-1-pro-benchmark/README.md) with a public
Azure SDK for Python clone and the pinned provenance commit. The large local
corpora are ignored, not bundled. It needs quota for roughly 374K input tokens
and incurs a paid model call; the captured benchmark needs neither.
Cross-site requests and arbitrary commands are rejected.
Real live errors stay errors; captures are never substituted for live output.
Cloud operations can incur charges. Follow each demo's own prerequisites.
Do not expose either local server through a public tunnel.

Live configuration: fill `AZD_AGENT_PROJECT_ENDPOINT` and `AZD_AGENT_NAME` for
the hosted agent; `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` for the Agent
Framework app; or `KIMI_ENDPOINT`, `KIMI_DEPLOYMENT`, and `KIMI_AUTH=cli` for
the sculpture. Sign in with `az login` and ensure inference access. Set
`SLIDEV_ENABLE_LIVE=1` only after configuration. fal also needs the
`Fal.EnableDeploy` registration, accepted fal terms, deployments, and confirmed
per-second prices; the fal slide shows its captured clip and has no live button.

The adapter loads `.env` on the server and passes those values to its fixed
runner subprocesses. Shell values take precedence. No keys or tokens enter
`VITE_*` variables or browser assets. A malformed project endpoint produces an
actionable live error without preventing static presentation startup.

Readiness check:

```powershell
Invoke-WebRequest http://127.0.0.1:3080 -UseBasicParsing | Select-Object StatusCode
Invoke-RestMethod http://127.0.0.1:8780/demo-api/health `
  -Headers @{'X-Demo-Client'='slidev'}
```

Request flow: slide button → same-origin Vite `/demo-api/` proxy →
loopback adapter with `X-Demo-Client: slidev` → fixed demo runner →
JSON live result or explicit error.

Foundry Local has no live demo on this hardware. fal access is enabled and all
five portfolio models are deployed in East US 2; one 5 s, 480P MiniMax H3 Max
Turbo clip was generated. The other four models have no output, so the deck
draws no cross-model speed, quality, or cost conclusion.

```powershell
npm run build
npm run typecheck
uv run --with python-dotenv --no-project python -m unittest test_demo_server -q
uv run --with playwright --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  --no-project python test_browser.py --output <session-capture-folder>
```

Browser checks use Microsoft Edge, inspect every slide in both themes at both
required resolutions, and check presenter notes. Captures belong outside Git.
First-party citations and speaking notes are in `slides.md`.

Demo slides omit redundant footnotes and operator notes. Full original
`caveats`, metrics, environment details, and provenance remain unchanged in each
`public/demos/<slug>/manifest.json`, the demo READMEs, and presenter notes.
Calendar labels use `MMM dd`; exact reporting boundaries and capture timestamps
remain in source evidence. Measured durations keep their original units.
The benchmark presentation removes supplemental disclaimer paragraphs from its
isolated display only; its captured HTML and data remain unchanged.

## Slide order

| Slides | Topic | Demo state |
| --- | --- | --- |
| 1–2 | Title, exact reporting window, four themes | Educational |
| 3 | azd Foundry bundle 1.0 GA | Workflow diagram |
| 4 | Foundry Local 2.3.0 / CLI 0.13.0 preview | Shared-cache diagram; hardware walkthrough |
| 5 | fal public-preview portfolio | Source-based comparison |
| 6–8 | Kimi K3.1 Pro, context scale, three.js and harder task | Three real scene settings; 3/3 bespoke benchmark trials, 33/33 exact fields |
| 9–10 | Agent Framework builder skills | Actual app capture; result 42, one tool call |
| 11 | Production improvement loop | Interactive pattern; Optimizer preview |
| 12 | Toolkit 1.6.19 | Three-feature comparison |
| 13 | Foundry Canvas and 1.0.19 notes caveat | Feature comparison |
| 14 | ThinkingBox | Illustrative state check + research chart |
| 15–16 | Runtime, deployment, SDK and REST migrations | Migration matrix |
| 17 | Exact-cutoff exclusions | Publication boundary |
| 18–19 | Code to hosted agent conversation | Actual recorded Inspector + hosted run; optional live invocation |
| 20 | Local coding conversation | Hardware walkthrough; no live run |
| 21–22 | Video model-choice conversation | Captured H3 Max Turbo clip with exact prompt; other four models not generated |
| 23–24 | MAI lifecycle conflict and coverage context | Dated source comparison |
| 25 | Close | Developer workflow synthesis |

The initial portfolio's exact MiniMax name is **H3 Max Turbo**, not the brief's
shortened H3 Turbo. The US-hosted announcement distinguishes Kling US Data Zone
from LTX/MiniMax Global Standard. The MAI 2.6 GA/preview source conflict remains
unresolved; the slides do not infer a new GA or downgrade.
The current November 9 Kimi catalog and Learn lifecycle table label version
2026-11-04 GA, contrary to the supplied brief's preview label. The deck dates
that current-status observation; it does not infer the historical catalog label
at the November 6 reporting cutoff.

The November 4 Agent Framework blog guide is the primary builder-skills
announcement; Microsoft Learn supplies companion implementation guidance.
Exact URLs and dates, including the November 5 Canvas 1.0.19 sync commit,
remain in presenter notes.
