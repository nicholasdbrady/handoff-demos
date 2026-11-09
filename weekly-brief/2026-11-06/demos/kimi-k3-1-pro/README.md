# Kimi K3.1 Pro: one prompt, three reasoning settings

For The Handoff, November 9, 2026. This demo sends the same kinetic-sculpture
prompt to a real Kimi K3.1 Pro deployment with `reasoning_effort` set to `none`,
`low`, and `high`. Each call returns a complete three.js document. The recorded
documents are unedited model output. The viewer adds isolation, not code fixes.

## Run from this repository

Prerequisites: Python 3.12+, uv, Azure CLI, and an Azure login with Foundry
inference access to a Kimi K3.1 Pro deployment. The live script uses OpenAI
Chat Completions because this model's catalog specifies chat completion, rather
than creating an agent or using the Responses API.

From `weekly-brief/2026-11-06`, copy the demo `.env.example` into your local
`.env`, or set these server-side environment variables:

```dotenv
KIMI_ENDPOINT=https://YOUR-RESOURCE.cognitiveservices.azure.com/openai/v1/
KIMI_DEPLOYMENT=kimi-k3-1-pro
KIMI_AUTH=cli
```

`KIMI_AUTH=cli` selects `AzureCliCredential`; omit it to use
`DefaultAzureCredential`. No keys are required. Run `az login` in the intended
tenant first. The runner reads the weekly folder's `.env` and then the demo's
`.env`, without overwriting exported values. No `VITE_` variables or credentials
reach the browser. Dependencies use uv's inline script metadata. If the default
feed cannot restore them, use
`uv run --index-url https://packagefeedproxy.microsoft.io/pypi/simple ...`.

```powershell
uv run demos/kimi-k3-1-pro/run.py --json --mode scene --effort none --max-tokens 12000
uv run demos/kimi-k3-1-pro/run.py --json --mode scene --effort low --max-tokens 12000
uv run demos/kimi-k3-1-pro/run.py --json --mode scene --effort high --max-tokens 12000
```

The runner prints one JSON object. It exits nonzero for API failure, truncation,
invalid scene HTML, or an incorrect factual answer. It never loads recorded
output as a fallback. Calls have a 120-second timeout and no retries.
`--record path.json` explicitly saves the real response and, for a complete
scene, its HTML source as a non-executable `.txt` alongside the JSON. Treat newly generated code as untrusted:
inspect it and use the isolation pattern in `viewer.html`, not an unrestricted
browser page.

The authored image question has a verifiable answer: **Copper, 240 particles**.
The image is a design chart, not model output.

```powershell
uv run demos/kimi-k3-1-pro/run.py --json --mode image --effort none --max-tokens 512
uv run demos/kimi-k3-1-pro/build_corpus.py --source D:\repos\azure-sdk-for-python
uv run demos/kimi-k3-1-pro/run.py --json --mode long --effort none --max-tokens 512
uv run demos/kimi-k3-1-pro/run.py --json --mode both --effort none --max-tokens 512
```

For another machine, pass its public Azure SDK for Python clone path. The corpus
builder reads committed, tracked Azure AI changelogs, not working-tree drafts.
It does not add an invented needle. Its index records source URLs, commit,
hashes, truncation, and the first actual Azure AI Projects release heading.
The captured check used 42,945 source characters and 9,240 service-reported
input tokens. Its answer, `2.10.0 (2026-10-30)`, matches the source. This is a
bounded retrieval check, **not** a million-token capacity benchmark.

## Show recorded scenes without Azure access

From `weekly-brief/2026-11-06`:

```powershell
uv run python -m http.server 8794 --bind 127.0.0.1 --directory public
```

Open `http://127.0.0.1:8794/demos/kimi-k3-1-pro/index.html`.
The deck can embed `/demos/kimi-k3-1-pro/index.html` from its own static server.
Select None, Low, or High, then Pause/Resume, drag to orbit, and change speed.
Expand **Exact shared prompt** to show the actual request. The source prompt
also lives in `prompt.txt`.

`viewer.html` loads the selected recorded document and the pinned local
three.js 0.160.1 runtime. Scene sources are stored as `.txt`, not directly
executable HTML routes. It inserts them into an `allow-scripts`-only iframe:
no same-origin grant, storage access, credentials, navigation permission, or
forms. Its CSP blocks all network calls. The wrapper refuses unexpected
external dependencies or active embedding elements. This is defense in depth,
not a claim that arbitrary generated code is trusted. Recorded scenes require
WebGL. The runtime's MIT license is in `vendor/LICENSE`.

## Recorded measurements

All three scene runs used the **same prompt** and a **12,000 completion-token
cap**, with no tools, temperature override, retries, or manual code repairs.

| Requested effort | Input | Output | Reasoning within output | Total | Time |
|---|---:|---:|---:|---:|---:|
| none | 347 | 4,486 | 0 | 4,833 | 18.780 s |
| low | 415 | 5,848 | 2,356 | 6,263 | 32.545 s |
| high | 415 | 10,550 | 6,423 | 10,965 | 62.332 s |

Reasoning tokens are **included in output tokens**, not added to total.
Input counts differ despite identical user text; these are the provider's
reported counts, not a locally estimated tokenizer result.
The API accepted all three settings. That does not establish a general ranking
or prove a proportional reasoning budget. There is one sample per setting.

The observed scenes differ: None has bright, dense orbital particles around
a compact sculpture; Low adds a taller stand and broad floor; High uses a
larger asymmetric ring composition and a different control layout. All three
render and animate, and their pause, reset, and speed controls work. Treat
these as observations of three samples, not evidence that High is better.

The image call used 1,130 input and 20 output tokens in 4.646 seconds and was
correct. The bounded corpus call used 9,240 input and 22 output tokens in
5.492 seconds and was correct.

Some attempts returned **"The specified endpoint does not exist"** despite
other successful calls to the same deployment. An early scene exhausted its
8,192-token output allowance; another returned incomplete HTML. These are
real limitations, not replay substitutions. Keep recorded scenes available
for the show; do not promise an uninterrupted live call.

## Model facts and dated evidence

Retrieved **November 9, 2026**. Reporting window cutoff: **November 6, 2026,
12:01 PST**. The weekly draft called the model preview. The current catalog and
retirement table say GA, but we do not have a historical catalog snapshot that
establishes its lifecycle label at the cutoff. Say: **"The Nov 5 announcement
introduced K3.1 Pro; the current catalog labels it GA."** Do not silently
rewrite the reporting-window claim.

| Fact | Primary evidence |
|---|---|
| Announced Nov 5; open-weight, text and images, up to 1M context | [Microsoft Tech Community announcement, Naomi Moneypenny](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292): "an open-weight model built for agentic work, with text and image understanding and a context window of up to 1 million tokens." This is not a Foundry devblog article. |
| Current lifecycle GA; chat completion; text/image in, text out | [Current model catalog](https://ai.azure.com/catalog/models/Kimi-K3.1-Pro): "Lifecycle Generally available (GA)", "Input type text, image". |
| Context/token limits | Catalog: "Context window 1048.576k", "Token limits 262.144k output". [Learn's Moonshot table](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#moonshot-ai-models-sold-by-azure) lists text/image input 1,000,000 tokens and text output 262,144 tokens. Use "roughly one million"; don't imply simultaneous maximum input and output were tested. |
| Deployment version and retirement | [Learn retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule#foundry-models-sold-by-azure): `Kimi-K3.1-Pro | 2026-11-04 | GA | 2027-11-04`. |
| Deployment type | Current management-plane model catalog advertises `MoonshotAI`, version `2026-11-04`, `GlobalStandard`; the captured deployment and inference succeeded in East US. No provisioned deployment was created. |
| Regions | [Learn region guidance](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability). The live model-capacity API returned 32 Global Standard regions on Nov 9: listed below. Only East US was deployed and called. Availability/quota can change. |
| Pricing | Nov 5 announcement table: **$2.30 input**, **$0.23 cached input**, **$11.50 output** per million tokens, USD. These are announcement rates, not an agreement-specific bill. |

Current Global Standard capacity locations: `australiaeast`, `brazilsouth`,
`westus`, `westus2`, `westeurope`, `southeastasia`, `westcentralus`,
`southcentralus`, `eastus`, `eastus2`, `canadacentral`, `japaneast`, `uksouth`,
`japanwest`, `koreacentral`, `francecentral`, `northcentralus`, `centralus`,
`southafricanorth`, `uaenorth`, `swedencentral`, `switzerlandnorth`,
`switzerlandwest`, `germanywestcentral`, `norwayeast`, `westus3`, `canadaeast`,
`polandcentral`, `southindia`, `italynorth`, `spaincentral`, `ukwest`.

The inference response's `model` field is **`Kimi-K3.1`**. The management-plane
deployment model is **`Kimi-K3.1-Pro`**, version **`2026-11-04`**. Preserve both
identifiers in narration and records.

## Created resources and cleanup

Created in the user-selected `foundry-devx-sub (nbrady)` subscription:

- Resource group: `rg-handoff-kimi-20261109`, East US.
- Foundry resource: `handoff-kimi-20261109`, `AIServices`, `S0`, managed identity.
- Model deployment: `kimi-k3-1-pro`, `MoonshotAI/Kimi-K3.1-Pro`, version
  `2026-11-04`, `GlobalStandard`, capacity 100 (100,000 TPM).
- Foundry User was granted to the signed-in caller **only on this new resource**.

Group and resource are tagged `handoff=2026-11-09`. No existing resource was
modified or deleted. No marketplace terms were accepted. No hosted agents,
search services, storage, or provisioned-throughput commitment were created.
The model deployment remains available for the show. There is no browser-side
subscription ID or resource key.

After the show, verify the group contains only this demo's resources, then
delete `rg-handoff-kimi-20261109` using the intended subscription. Do not run
cleanup before the presenter is finished. Remove only this demo's local `.env`
and rebuilt corpus if no longer needed.

## Validate and refresh records

```powershell
uv run demos/kimi-k3-1-pro/test_demo.py
uv run demos/kimi-k3-1-pro/build_report.py
```

`build_report.py` combines successful records and source provenance into
`recorded-results.json` and `manifest.json`. It refuses mismatched prompts.
Only refresh those artifacts after explicit live calls have succeeded; the
builder does not perform inference. Browser checks are recorded separately.
The scene `correct` field is intentionally null: rendering and working controls
are tested, but artistic quality is not a binary factual answer.

The wrapper's single-font loading/error message is intentional; it has no
content hierarchy to split. Its 18px text follows the established live-demo
density. The comparison surface uses the shared sans family for labels and
mono for measurements. Generated scene styling is preserved as model output,
not polished to remove its differences.
