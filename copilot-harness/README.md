# Copilot harness

A 20-slide presentation about Microsoft Copilot harness in Microsoft Foundry.
Start with the portable slides and synthetic chat fixtures. Enable live recipe
calls separately with your own Foundry project.

## Present the slides

From the repository root, use Node.js 22.12 or later:

```powershell
Set-Location copilot-harness
npm ci --registry=https://packagefeedproxy.microsoft.io/npm/
npm run dev
```

Open <http://127.0.0.1:3070>. Presenter notes are at
<http://127.0.0.1:3070/presenter>. Stop with Ctrl+C. This path does not need
Python, Azure credentials, or an adapter. Dependencies must be installed before
offline use.

On slide 12, use **Replay** to inspect the two chat lanes. Slides 15 and 16
also use synthetic fixtures. Each fixture says **SYNTHETIC** and reports no
measured service latency, token usage, tool execution, cost, or generated files.
These fixtures are not recordings of real runs. Regenerate them with
`python prepare_fixtures.py` if needed.

The deck keeps the historical folder name `public\recordings` for replay
compatibility. Only explicitly synthetic fixtures are shipped. No runtime
captures from the source repository were imported.

## Enable live recipe calls

Use Python 3.13, `uv`, and your own existing Foundry project, supported model
deployment, and two configured agents. The demo does not provision infrastructure.
Review regional availability and preview limits in the linked first-party
sources before setup. Model calls and tools can incur Azure charges.

```powershell
# Run inside copilot-harness
uv venv --python 3.13 .venv
uv pip install --python .venv\Scripts\python.exe `
  --index-url https://packagefeedproxy.microsoft.io/pypi/simple -r requirements.txt
Copy-Item .env.example .env
```

Set `AZURE_AI_PROJECT_ENDPOINT` to your HTTPS project URL, for example
`https://your-account.services.ai.azure.com/api/projects/your-project`.
Set `FOUNDRY_MODEL_DEPLOYMENT_NAME` and both agent names to your deployment and
agents. Sign in with `az login` using an account with the required project
access. **This adapter uses Microsoft Entra authentication, not an API key.**

```powershell
.\start.ps1 -Live
```

The script starts the loopback adapter on port 3071 and slides on port 3070.
Wait for background authentication readiness, then select **Live** on slide 12.
Only an explicit Send invokes inference. Failures stay visible; a synthetic
fixture is never substituted for a live failure. Stop stops receiving the stream;
server-side work can finish. Wait for the model slot before sending again.

With live disabled, `.\start.ps1` runs the same adapter without contacting Azure.
For a separate adapter terminal:

```powershell
.\.venv\Scripts\python.exe demo_server.py
```

Set `SLIDEV_ENABLE_LIVE=1` in `.env` only when intentionally running live calls.
Do not expose either port with a public tunnel.

## Run the Python example directly

```powershell
# A real compatibility call to your configured agent; incurs usage.
.\.venv\Scripts\python.exe copilot_harness_factory.py probe --lane copilot
```

The factory also has `create` and `record` commands. **Create changes cloud
state:** it creates versions of both named agents and a review skill. Review
names, permissions, model availability, and cost before using it. It does not
create a project, model deployment, or role assignment.

`record` makes a real call and writes responses and downloaded files beneath
`public\recordings`. Treat all new captures as private until reviewed. Do not
commit them. Generated notebook validation is structural and syntax-only;
the generated cloud calls must not execute. File downloads require the agent
identity to have project access; the presenter's own access is not equivalent.

## Configuration

| Variable | Requirement |
| --- | --- |
| `AZURE_AI_PROJECT_ENDPOINT` | Required for live calls; HTTPS project URL, not resource-root OpenAI URL |
| `FOUNDRY_MODEL_DEPLOYMENT_NAME` | Your compatible deployment; default `gpt-6-luna` |
| `DEFAULT_AGENT_NAME` / `COPILOT_AGENT_NAME` | Your prepared agent names |
| `SLIDEV_ENABLE_LIVE` | Default `0`; opt in with `1` or `start.ps1 -Live` |
| `INPUT_USD_PER_MILLION` / `OUTPUT_USD_PER_MILLION` | Optional verified token prices; blank means unknown cost |

Keep `.env` local. Do not use `VITE_*` for secrets.

## Boundaries

- Hosted SDK and Agent Framework runtimes are **not included**. Their slides
  illustrate the interface with synthetic fixtures and offer no live controls.
- Fusion and DeepSWE require a separate backend that is **not included**.
  Slide 19 is a disabled explanation, with no proxy to another local service.
- The source rehearsal had a notebook upload failure and a managed run with
  zero downloadable file IDs. Do not promise downloadable files for every run.
- Live cloud calls, hosted execution, Fusion, and OBO were not verified in this
  portable export. The source's completed runs are not evidence for this copy.
- Slidev 53's Twoslash/FloatingVue integration emits a known `Popper` console
  error in development. Slide rendering and fixture interactions work, but the
  console is not clean. Browser evidence retains that error; unexpected errors fail.

## Checks

```powershell
npm run build
npm run typecheck
node --test test_chat.cjs
.\.venv\Scripts\python.exe -m unittest test_demo
```

`test_browser.py --output <folder>` checks portable synthetic mode using installed
Microsoft Edge. It checks the disabled Fusion slide and fails on unexpected browser errors.
It must not be used as evidence of live service execution.

## Sources

- [Copilot harness tools, skills, portal, azd, and SDK](https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness)
- [Regions, quotas, and limits](https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions#microsoft-copilot-harness-preview)
- [Versioned Foundry skills](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills)

See the repository provenance notice for source and redistribution limits.
