# The Handoff: weekly Foundry news brief

24-slide developer briefing for November 9, 2026. Reporting window:
October 30 13:01 PDT through November 6 12:01 PST.

You need Node.js 22.12 or later and npm. Python 3.11+ and
[uv](https://docs.astral.sh/uv/) are needed for the optional adapter; individual
demos can require a newer Python version, Azure CLI, or azd 1.37+.

```powershell
git clone --branch nicholasdbrady-weekly-brief-nov-9 https://github.com/nicholasdbrady/handoff-demos.git
Set-Location handoff-demos\weekly-brief\2026-11-06
npm ci --registry=https://packagefeedproxy.microsoft.io/npm/
Copy-Item .env.example .env
npm run dev
```

Open http://127.0.0.1:3080 or http://127.0.0.1:3080/presenter for notes.
The static explanations need no cloud access. Four demo panels read their own
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
350-second timeout. Cross-site requests and arbitrary commands are rejected.
Real live errors stay errors; captures are never substituted for live output.
Cloud operations can incur charges. Follow each demo's own prerequisites.
Do not expose either local server through a public tunnel.

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

Foundry Local has no live demo on this hardware. fal generation is unavailable
without approved access and terms; the educational portfolio comparison remains.

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

## Slide order

| Slides | Topic | Demo state |
| --- | --- | --- |
| 1–2 | Title, exact reporting window, four themes | Educational |
| 3 | azd Foundry bundle 1.0 GA | Workflow diagram |
| 4 | Foundry Local 2.3.0 / CLI 0.13.0 preview | Shared-cache diagram; hardware walkthrough |
| 5 | fal public-preview portfolio | Source-based comparison |
| 6–7 | Kimi K3.1 Pro and context scale | Manifest-based capture panel |
| 8–9 | Agent Framework builder skills | Actual app capture; result 42, one tool call |
| 10 | Production improvement loop | Interactive pattern; Optimizer preview |
| 11 | Toolkit 1.6.19 | Three-feature comparison |
| 12 | Foundry Canvas and 1.0.19 notes caveat | Feature comparison |
| 13 | ThinkingBox | Illustrative state check + research chart |
| 14–15 | Runtime, deployment, SDK and REST migrations | Migration matrix |
| 16 | Exact-cutoff exclusions | Publication boundary |
| 17–18 | Code to hosted agent conversation | Manifest-based azd capture panel |
| 19 | Local coding conversation | Hardware walkthrough; no live run |
| 20–21 | Video model-choice conversation | Explicit unavailable generation; comparison |
| 22–23 | MAI lifecycle conflict and coverage context | Dated source comparison |
| 24 | Close | Developer workflow synthesis |

The initial portfolio's exact MiniMax name is **H3 Max Turbo**, not the brief's
shortened H3 Turbo. The US-hosted announcement distinguishes Kling US Data Zone
from LTX/MiniMax Global Standard. The MAI 2.6 GA/preview source conflict remains
unresolved; the slides do not infer a new GA or downgrade.
