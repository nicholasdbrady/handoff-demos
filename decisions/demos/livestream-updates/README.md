# Foundry developer livestream, in Slidev

A 25-slide, 16:9 presentation (22 core + 3 appendix) for the Azure OpenAI Decisions API, the Microsoft
System One API, and agent on-behalf-of-user (OBO) tool connections in Foundry
Agent Service. Seven demo panels and a two-stage code walkthrough run **inside the slides** against live services,
through a loopback-only Python adapter. Each slide has speaker notes; source
links are in the notes as `Source:` lines. Allow about 40 minutes.

## Start the presentation

Use two terminals from the repository root. Node.js 22.12+ and `uv` are required.
Configure `.env` first (see [Enable live calls](#enable-live-calls)).

Clone the whole `handoff-demos` repository and enter `decisions\`, not just this folder. The adapter
imports the sibling `demos\decisions-api` and `demos\agent-obo-tools` demos. Run
locally; a published static deck cannot execute the Python examples.
Each person uses their own Azure resource and either Microsoft Entra sign-in or
their own API key. See [Choose model authentication](#choose-model-authentication).

```powershell
# Terminal 1: local Python adapter
uv run --no-project --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  --with-requirements demos\livestream-updates\requirements.txt `
  python demos\livestream-updates\demo_server.py
```

```powershell
# Terminal 2: slides and Vue UI
Set-Location demos\livestream-updates
npm ci --registry=https://packagefeedproxy.microsoft.io/npm/
npm run dev
```

Open **http://127.0.0.1:3030**. Presenter notes are at
**http://127.0.0.1:3030/presenter**. Arrow keys navigate; keyboard events inside
the demo controls stay in those controls. Stop each server with Ctrl+C.
The navigation toolbar opens from the bottom edge or on keyboard focus,
so its hidden hit area does not cover the demo buttons.

The presentation uses port 3030 and the adapter uses port 8765. Both bind to
`127.0.0.1`. Do not use `--remote`, public tunnels, or a public backend deployment.
On start, the adapter signs in once in the background. It then renews the
Microsoft Entra token in the background before it expires, so no measured call
includes sign-in time. API-key mode does not start an Entra sign-in.

## Before the stream

1. Fill `.env`, set `SLIDEV_ENABLE_LIVE=1` and `SLIDEV_ENABLE_CODE_RUN=1`, and
   start both servers.
2. Open slides 3, 5, 6, 8, 9, 11, 12, and 19. Missing configuration appears beside the
   examples; configured panels do not show a connection badge.
3. Run the core demo panels once to confirm deployment and tenant access. Slide 9's
   extraction checks are local; only **Route note with Luna** sends a model request.
4. Provision the OBO agent and tool connection. Test sign-in and consent with
   a test account before you share your screen.
5. Use test accounts and synthetic data only. Keep Microsoft sign-in windows
   off the broadcast.
6. Run demos from the main slide window, not presenter view.
7. If a live dependency fails during the stream, say so and leave the error
   visible. There is no automatic fallback.

The static build (`dist\`) has no backend; its demo panels report that the
backend is unavailable.

## Slide map

| Slide | Title | Runs live |
| --- | --- | --- |
| 1 | Decide on evidence. Act with the user. | |
| 2 | What's new | |
| 3 | System 1 and System 2 on the same ticket. | `SystemCompare.vue` |
| 4 | What a decision model is—and is not. | |
| 5 | One call. Three answer shapes. | Two editable Monaco stages |
| 6 | Turn answers into a route. | `DecisionDemo.vue` |
| 7 | The uncertain path is part of the design. | |
| 8 | Inspect the suitcase. Then change the trip. | `ImageDecisionDemo.vue` |
| 9 | From a packing slip to a receiving exception. | `RetailReceivingDemo.vue`; synthetic extraction, optional live semantic call |
| 10 | Pick the API, not just the model name. | |
| 11 | Microsoft-Decision-1: the native request. | `MicrosoftDecisionDemo.vue` |
| 12 | Same product—or a costly mistake? | `ProviderCompare.vue` |
| 13 | A judgment is not permission. | |
| 14 | Now the agent needs the user's data. | |
| 15 | Three boundaries. Three separate decisions. | |
| 16 | Which identity is the OBO actor? | |
| 17 | Configure both sides of the boundary. | |
| 18 | Consent is a resumable step, not a dead end. | |
| 19 | Call the agent as the user. | `OboDemo.vue` |
| 20 | The proof is an access test, not a profile. | |
| 21 | A model judges. Your code decides. The service authorizes. | |
| 22 | Keep the code. Keep the sources. | |
| 23 | Appendix: One input. Many independent questions. | |
| 24 | Appendix: Measure your workload, not the headline. | |
| 25 | Appendix: One category. Different model surfaces. | |

### Slides 3–4: decision models, System 1 and System 2

Slide 3 demonstrates the contrast; slide 4 explains what a decision model is
and is not. The System 1 and System 2
framing comes from Daniel Kahneman and TypeSafe's
[System One concept page](https://docs.typesafe.ai/concepts/system-one). The
deck credits it in the notes; these are not Azure product names.

Slide 3 sends the same ticket to two lanes in parallel with **Run both**:

- **System 1 (left):** one Decisions API request with three questions
  (`wants_refund`, `team`, `severity`). It shows distributions, the score, and
  token counts.
- **System 2 (right):** the Responses API with `reasoning.effort: high` and
  `reasoning.summary: auto`. It shows the reasoning summary, the written
  answer, and output and reasoning tokens.

Each lane has its own clock and shows its result when its request finishes.
Both lanes use `DECISIONS_DEPLOYMENT` unless you set `SYSTEM2_DEPLOYMENT`.
Times vary with network, load, and input; the token difference is the
consistent signal. On 26 October, 23 Decisions calls from one client took
0.6-4.4 s, so System 1 can finish second. Reasoning summaries are best effort,
so some runs return none.

Under each clock, a live run shows an estimated cost per 1,000 runs. The
adapter computes it from the run's token usage at the Azure retail list price
for `gpt-6-luna`, Global Standard, short context (`PRICES` in
`demo_server.py`, from the [Azure Retail Prices API](https://prices.azure.com/api/retail/prices),
effective 1 September 2026). The Decisions documentation does not give a
separate price, so the Decisions estimate uses the same token rates. Rehearsal
runs and models without a price show no cost. Hover the value to see the cost
of the single run.

The **Result / Code / JSON** switch in the toolbar changes both lanes:

- **Code** shows the Python SDK call each lane sends for the current ticket.
  The adapter builds it from the same request builders the lanes use, and
  shows it without a call to Azure. Change the preset or edit the ticket to
  update it.
- **JSON** shows the response body each lane received, as the SDK parsed it.

### Runnable code on slide 5

The code editors run Python on your machine. Select **Run** to send the editor
text to the loopback adapter. The adapter starts a new isolated Python process
(`code_runner.py`) for each run. That process gets two names: `client` and
`DEPLOYMENT`.

**One predicate / Three answer shapes** switches the same slide between two
editable examples. Switching never makes a model call. The second stage is
also accessible with the slide's next-click navigation.

- Code runs are off by default. Set `SLIDEV_ENABLE_CODE_RUN=1` in `.env` and
  restart `demo_server.py`. Only the local deck origin can call the endpoint.
  One run at a time; each run stops after 75 seconds. The code has your user
  account's access, so do not print environment variables or secrets on stream.
- Editing never sends a request (`autorun:false`). Only **Run** does.
- Presenter-view editors are separate copies and do not sync edits or output.
- `slidev build` and `slidev export` render these blocks as static code.

### Live behavior

Inference buttons call the configured services. The retail extraction and exact
checks use labeled synthetic fixtures without an extraction-service call. Errors stay errors: the adapter
never replaces a failed live call with synthetic output. The adapter keeps a
synthetic test client (`mode: "rehearsal"`) for automated tests only; the deck
does not offer it.

Live OBO uses the agent-blueprint audience. The panel performs a fixed
read-only Work IQ `fetch` request for the user's `/me` profile; use a read-only MCP connection and a
test account for the stream.

The original CLI demos still provide optional cache and latency experiments.
The new image panels use bundled synthetic fixtures rather than the CLI's
proof-of-delivery scenario.

### Slides 8–12: images, retail evidence, and provider contracts

The two verified Foundry paths are different APIs, not a model-name switch:

| Surface | Endpoint suffix | Request / response | Clients |
| --- | --- | --- | --- |
| Azure OpenAI Decisions (`gpt-6-luna`) | `/openai/v1/decisions` | `input`, questions array, `predicate`/`choice`/`score`; answers array | OpenAI Python >=3.26.0; JavaScript >=7.30.0; REST |
| Microsoft-Decision-1 | `/providers/microsoft/v1/systemone` | `state`, named questions object, `noul`/`choice`/`score` and `criteria`; named answers object | TypeSafe Python / TypeScript SDKs (text/Noul wire compatibility tested); REST |

Both document resource-endpoint inference with a deployment name and either
API-key or Entra authentication. Do not silently convert a project endpoint
or assume instant model-name invocation works on either route. A dedicated
Foundry SDK System One method is not claimed. TypeSafe SDK wire compatibility
is a separate integration. See the
[Decisions how-to](https://learn.microsoft.com/azure/foundry/openai/how-to/decisions)
and [Microsoft-Decision-1 how-to](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision).

Slide 11's **Python** and **TypeScript** views show minimal TypeSafe SDK samples
with Azure Identity, literal placeholder resource URLs and deployment names,
and compression disabled. Sign in with `az login` and install `typesafe-sdk`
and `azure-identity` for Python, or `@typesafe-ai/sdk` and `@azure/identity`
for TypeScript. The Entra token is supplied through the SDK's
`api_key`/`apiKey` bearer credential setting; these short-lived samples do not
implement token renewal. Python `typesafe-sdk` 0.7.5 and `@typesafe-ai/sdk`
0.7.0 were live-tested with text/Noul against the Azure deployment.
The samples are copyable listings, not executable editor runners.
**Run Decision-1** makes the optional live call through the existing local
adapter using the same state and questions; it does not execute the displayed SDK code.
The image, native, retail, and provider-comparison panels show **Total elapsed**:
the full browser wait, frozen when each request completes or fails. The main
clock never switches to a narrower measurement. **API round trip** is shown
separately after success: the adapter's measured provider call, including network
time but excluding earlier authentication, local setup, or queueing. It is not
pure model inference. Sub-second results use milliseconds. Each panel also
shows estimated USD per 1,000 equivalent runs.
Both suitcase modes share these metrics. Rehearsal has no
billable estimate; missing usage or an unknown model price shows cost unavailable.
Decision-1 uses the Azure Retail Prices API's West US3 Global meter:
USD0.042 per million tokens, effective October 1, 2026, retrieved October 29.
Source: https://prices.azure.com/api/retail/prices (Microsoft Decision Models).
The image estimate uses the existing model-specific token rates, including
cache usage when returned. These are estimates, not invoices or benchmarks.

**Response** opens automatically after Run and displays the noul probability,
selected team, and fractional severity score on its 0-to-3 scale.
**JSON** preserves its native answer object. All four views fill the
remaining slide height inside the outer padding; long code and JSON scroll
within that space. Editing the ticket clears the old response. The example uses text,
not images. No Microsoft-Decision-1 image support is claimed.
The model overview labels Laya and Jev as wider ecosystem examples, not
verified managed Foundry offerings; it is not an exhaustive catalog.

The deck follows the system light/dark preference by default. Slidev's theme
toggle can override it; interactive controls, code panels, and results use the
same theme. Chapter slides retain their dark emphasis in either mode.

Slide 8 uses original, AI-generated photorealistic suitcase fixtures:
sunshine, rain, and obscured. Exact generation prompts, PNGs, and provenance are in
[`public\packing\`](public/packing/README.md). No third-party artwork is copied.
The earlier generated mug fixtures remain unused; they are not sent by these panels.
Image-only input contains an `input_image` part; the question instructions
define what to inspect: rain protection, footwear, and evidence quality.
Use the left/right carousel arrows to switch among the three suitcase scenarios.
On slide 8, select a question beneath the image and edit its instructions before
Inspect. These edits change that question in the actual request and Python view;
question names, types, and answer choices stay fixed. Select **Add a trip brief**
to keep the selected image, restore the original inspection questions, and edit the trip brief.
This mode adds the brief as `input_text` and a 0-to-2
trip-fit score. Both modes provide **Answers / Python / JSON** views and probability
bars. The Python view shows local file encoding and the exact code-controlled
routing rule; the existing runner/setup provides `client`.

Keep Sunshine kit selected, run Beach weekend, then select **Plot twist: rain**
and run again. Pixels stay fixed while context changes. Try Rain kit and Under
cover next. These are teaching inputs, not accuracy or calibration evidence.
Code requires clear evidence and quality/fit confidences >=0.65, then maps a fit
score >=1.5 to Ready; lower fit to Repack. Refusal, missing/invalid decision
fields, obscured evidence, and low confidence route to review. Thresholds are
illustrative, not safety guarantees. No automatic action is taken.
Changing an image, inspection instructions, or brief clears stale output. No automatic
model call occurs on selection, navigation, or opening the code view.
The practical analogy is packing evidence plus order requirements, or a
technician's kit plus a work order. Keep exact counts and arithmetic in code.

### Slide 9: retail receiving evidence

The generic retail scenario uses a synthetic packing slip plus a structured order
and receiving record. It is not customer-specific and does not invoke OCR,
Document Intelligence, or Content Understanding. Its normalized source regions
and confidence values are illustrative fixtures, not a native extraction response.
Code computes **12 − 10 = 2 cases short**, then **2 × USD18.50 = USD37.00**
as a reference value, never a payable claim.

Changing the scenario runs only local checks. Low OCR/field confidence, missing
source regions, parsing failures, unit/currency mismatches, and contradictory
quantities force review before inference. A structured reason code skips inference.
Only **Route note with Luna** sends the ambiguous note for a semantic choice.
The 0.9 source gates and 0.8 choice-confidence gate are illustrative, not calibrated.
A model probability cannot override the evidence gates. Native DI/CU source regions
usually remove the need for another box-finding stage. Recognition confidence,
field confidence, semantic probability, choice confidence, and geometry are not
interchangeable or combined into one score.

### Slide 12: Luna versus Microsoft-Decision-1

**Run 12 pairs** processes an original synthetic catalog-matching set automatically:
one request at a time per provider, with the two provider series running in parallel.
Both receive identical text attributes, instructions, and same/different/review choices.
The adapter translates native `state`/`criteria` into Luna `input`/`choices`.
Photos are decorative, not sent to either model, and do not establish product identity.
Selecting a row shows the records, authored reference, and its explanation. Names may
be aliases; confirmed capacity, color, generation, connection, memory, or pack conflicts
mean different sellable variants. Missing decisive information without a conflict means
review. Equivalent notations such as GB and gigabytes do not change the variant.

Progress, whole-batch elapsed time, returned pairs/second, reference-label matches, and
estimated USD per 1K pairs update independently. Reference labels, reasons, images,
and scenario titles never enter model input. Errors/refusals/invalid answers do not
count as matches. Each failed item remains inspectable; the series continues.
Cost is the sum of all 12 usage estimates divided by 12, then multiplied by 1,000.
Any failed call or missing usage makes cost unavailable. API calls total is a separate
sum of backend request durations and never replaces the full browser timer.
**Request** shows exact wire payloads; **JSON** keeps each selected pair's native response
or actionable error. Re-running resets both lanes; inspecting rows does not reset them.
No failure falls back to synthetic answers. Offline tests explicitly use rehearsal,
which is labeled and reports no billable cost or model-quality/throughput claim.
This small authored set is not a quality benchmark; no provider winner is assumed.
Both deployments must already exist. No cloud resources or catalog merges occur.
Inspired by [TypeSafe entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment).
Product photo sources and license are in `public/catalog/CREDITS.md`.

## Enable live calls

```powershell
Copy-Item demos\livestream-updates\.env.example demos\livestream-updates\.env
```

Fill the new `.env` locally, then restart the adapter. Do not put credentials in
`VITE_*` variables, Markdown, Vue, screenshots, or Git.
The deck's `.env` overrides inherited environment variables. This keeps a
resource configured for another project from silently taking precedence.
Leave `AZURE_OPENAI_API_KEY` empty to use Microsoft Entra authentication.

### Choose model authentication

These settings cover Decisions, both lanes on slide 3, the triage panel, and
the Monaco Run buttons. Set `AZURE_OPENAI_ENDPOINT` to your Azure resource
root, such as `https://your-resource.openai.azure.com`, without `/openai/v1/`.
The code appends that path. Set `DECISIONS_DEPLOYMENT` to your Decisions-enabled
deployment name. Check the current
[Decisions availability](https://learn.microsoft.com/azure/foundry/openai/how-to/decisions);
authentication alone does not enable the preview.

| Method | Local `.env` setting | What you need |
| --- | --- | --- |
| Microsoft Entra via `azure-identity` | Leave `AZURE_OPENAI_API_KEY=` empty | Sign in with `az login --tenant <your-tenant-id>`. The signed-in identity needs **Cognitive Services OpenAI User**, or an equivalent inference role, on your resource. |
| Your Azure API key | Set `AZURE_OPENAI_API_KEY` to your resource key | A resource that permits local/key authentication. Azure CLI sign-in is not required for model calls. |

A nonempty key takes precedence. Failed key calls stay failures; they do not
silently switch to Entra. An empty key selects `DefaultAzureCredential`, which
can also use a configured managed identity or other supported Azure credential.
`azure-identity` is already in `requirements.txt`. Restart the Python adapter
after changing credentials, endpoints, or model settings.
The client follows Microsoft's
[Azure OpenAI authentication examples](https://learn.microsoft.com/azure/developer/ai/how-to/switching-endpoints#authentication).

Optional: set `SYSTEM2_DEPLOYMENT` for slide 3's reasoning model. Its fallback
is `RESPONSES_DEPLOYMENT`, then `DECISIONS_DEPLOYMENT`. Both lanes use the same
endpoint and credential. The slide code receives the configured `client` and
`DEPLOYMENT`; viewers do not paste credentials into the editor.

You can run the model demos without configuring OBO. Leave its settings blank;
only the OBO panel will report missing configuration.

### Optional Microsoft-Decision-1 setup

Deploy `Microsoft-Decision-1` on a Foundry resource using its
[deployment how-to](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision).
This deck does not provision a deployment. Set:

```dotenv
SYSTEMONE_ENDPOINT=https://your-resource.services.ai.azure.com
SYSTEMONE_DEPLOYMENT=your-decision-1-deployment-name
```

Use the resource root, not a project URL or a full API path. If
`SYSTEMONE_ENDPOINT` is empty, the adapter reuses `AZURE_OPENAI_ENDPOINT`;
this works only when that resource hosts the deployment.
If `SYSTEMONE_API_KEY` is absent, the adapter reuses `AZURE_OPENAI_API_KEY`.
Set a separate resource key explicitly when needed. Set `SYSTEMONE_API_KEY=`
explicitly to select Entra even if OpenAI uses a key. The Entra scope is
`https://cognitiveservices.azure.com/.default`; the identity needs inference
access on the selected resource. Failed key calls do not retry with Entra.

Restart the adapter, then open slide 11. Its generated standalone Python
example uses the three `SYSTEMONE_*` settings explicitly: set the endpoint
even when the local adapter could reuse the OpenAI setting. Keys and tokens
stay on the Python side. Configuration readiness is not proof of deployment
availability. A missing deployment disables this panel only.

### OBO requires a user, not a model key

For OBO:

- First provision and authorize the existing agent using the instructions in
  [`..\agent-obo-tools\README.md`](../agent-obo-tools/README.md).
- Set the project endpoint, agent name, tenant ID, public client app ID, and
  blueprint client ID. The client app needs delegated `access_agent` permission
  and a `http://localhost` redirect URI.
- Complete downstream consent or preauthorization as required by the tool and
  tenant. Verify preview setup against your tenant; the original setup script's
  configurable ARM API version has not been verified with a live deployment.
- Set `OBO_CONSENT_HOSTS` only to verified product-owned consent hosts. The
  default permits `consent.azure-apim.net`; unexpected hosts fail closed.

`AZURE_OPENAI_API_KEY` authenticates model calls only. It cannot authenticate
this OBO flow. Agent setup uses Entra and project RBAC; runtime uses
`InteractiveBrowserCredential` for the agent blueprint's
`api://<blueprint-client-id>/access_agent` scope. Signing in to Azure CLI for
model calls does not replace that delegated user sign-in. See
[Configure user delegation](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-user-delegation).

Set `SLIDEV_ENABLE_LIVE=1` and reload the slide after restarting the adapter.
Readiness is checked when a panel mounts and reports configuration presence, not successful
authentication or feature availability. The OBO panel lists missing setting
names without displaying their values. Configuration presence does not prove
that the agent, tool connection, or delegated permissions exist; the service call checks those.

Microsoft sign-in and consent open in a **separate browser flow**, not an iframe.
Complete sign-in yourself. The deck does not collect passwords, expose bearer
tokens, or grant permissions. Consent links are held in memory and are not
logged. The returned agent text is hidden until you select **Reveal response**.

**Reset session** closes the local HTTP client and forgets its response ID. It
does not revoke tenant consent or sign out of Microsoft in your browser. Choose
the second account during the next sign-in flow when testing user isolation.

### Authentication troubleshooting

| Symptom | Check |
| --- | --- |
| Entra sign-in fails | Leave the model key empty; sign in to the resource's tenant and check the selected `DefaultAzureCredential` source. |
| Model API returns 401 or 403 | Check the key and whether key auth is enabled, or check the Entra identity's inference role. Model credentials do not grant OBO access. |
| Model API returns 404 | Use the resource root and your deployment name; check that the resource supports the Decisions API. |
| Slides load but Run cannot reach the server | Start `demo_server.py` on port 8765 and use the local deck on port 3030, not the static export. |

Both authentication paths are covered by offline tests with synthetic
credentials and in-memory HTTP transports. They exercise the panel and Monaco
client builders for Decisions and Responses, check key precedence and the
Entra scope, and ensure the OBO client still uses delegated sign-in. No cloud
resource, real key, or user consent is needed for those tests.

## Edit, update, and extend

| File | Change here |
| --- | --- |
| `slides.md` | Story, code samples, and speaker notes (with sources) inside HTML comments |
| `components\*.vue` | Form controls, result rendering, consent and reveal interactions |
| `demo-api.ts` | Typed browser API contract, readiness, and visible error handling |
| `demo_server.py` | Server-side calls to the existing Python demos |
| `style.css` | Locally hosted font, colors, layouts, focus styles, readable demo output |
| `vite.config.ts` | Same-origin proxy to the loopback adapter |

Run `npm run dev` while editing; Slidev hot reloads Markdown and Vue.
Slide separators are `---`. A file in `components\` is auto-imported into slides.
Do not embed Python or Azure credentials in browser-side code.

### Official Slidev agent tooling

The official **`slidevjs/slidev`** skill was installed in the workspace under
`.agents\skills\slidev` with the `skills` CLI, targeting GitHub Copilot.
The skill is local/ignored; `skills-lock.json` records its source. Restore it with:

```powershell
# Repository root, using your approved npm proxy configuration
npm exec --yes --package=skills -- skills add slidevjs/slidev `
  --skill slidev --agent github-copilot --copy --yes
```

Slidev 53 also ships its own MCP server; no third-party server is needed:

```powershell
# From this deck's directory
npm run mcp
```

This starts a **stdio MCP server** for inspecting, editing, inserting, moving,
and removing slides. Configure that command in an MCP-capable client if needed.
The dev-server HTTP MCP endpoint is **disabled** in `slides.md` with `mcp: false`
because this presentation also has credentialed demo controls.
See [Slidev's AI authoring guide](https://sli.dev/guide/work-with-ai).

### npm proxy authentication

All package resolution for this deck used the Microsoft npm proxy. If npm gets
`E401` while an unauthenticated proxy metadata request succeeds, check stale
proxy credentials in your npm configuration. Do not switch to public npm.
Also preserve the tarball URLs returned by the proxy; indiscriminate host
rewriting can turn the proxy's approved Azure feed URL into a nonexistent path.

## Validation

```powershell
Set-Location demos\livestream-updates
npm run typecheck
npm run build
uv run --no-project --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  --with-requirements requirements-dev.txt python -m unittest test_demo_server test_retail_receiving test_catalog_matching -v
# With both servers running, SLIDEV_ENABLE_CODE_RUN=1, and Microsoft Edge installed:
uv run --no-project --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  --with-requirements requirements-dev.txt python test_browser.py
```

The browser test uses headless Edge at 1920x1080 and 1280x720. It stubs
readiness and rewrites each request to the adapter's test client, so it makes
no Azure calls. It checks layout and toolbar collisions on all 25 slides, the
System 1 and System 2 lanes (including one lane failing alone, the Code and
JSON views, the cost labels, and the reasoning-summary layout), both code
editor stages, the triage threshold, native Microsoft SDK listings and JSON,
all three suitcase fixtures, editable briefs and plot twists, retail evidence gates,
independent provider lanes and native contracts, the OBO consent and reveal flow, the
not-connected state of every panel, API failure handling, and presenter notes.

Add `--live-decisions` to make **billable Azure OpenAI calls** with synthetic
text: one **Run both** on slide 3, two triage runs on slide 6, and one run of
each code editor. It never invokes OBO or approves consent.
Add `--live-packing` to make five **billable Azure Decisions calls** with the
bundled synthetic suitcase photos: image-only, sunshine/beach, sunshine/rain,
rain/rain, and obscured/rain. It checks the observed beach/rain fit contrast
and requires obscured evidence to route to review. It does not assert
universal image accuracy or force a Ready result.
Use `--capture-dir <folder>` to keep screenshots and response data.

Unit tests cover typed Decisions output, both System lanes, live opt-in,
cross-site rejection, per-browser continuation, consent retries, reset,
consent host checks, and the slide code runner. Live model availability,
tenant consent, and two-user data authorization still require a real Azure
rehearsal.

The installed Slidev dependency stack logs a caught `Failed to patch
FloatingVue` warning in development; it comes from the Twoslash hover
integration, not the demo panels. Do not suppress other browser errors.

## Content choices

- Separates documented capability from announcement timing: a documentation
  update date is not asserted as the first public announcement.
- Uses "probability estimate" and "confidence", not a blanket calibration claim.
- Paraphrases the System 1 and System 2 framing and credits its sources;
  does not repeat third-party performance claims.
- Avoids applying OpenAI public API prices to Azure or promising a universal
  speedup. Measures latency only for actual live calls.
- Separates management, endpoint, and downstream authorization; avoids claiming
  that OBO removes all other standing permissions an agent might have.
- Keeps a refusal, failed tool call, missing answer, and missing consent visible.
- Uses an actual flow arrow in the CSS diagram; the 2px arrowhead is geometry,
  not a decorative card-side accent.
