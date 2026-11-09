# fal video: fast draft or final render?

**Show the source-based comparison. Do not run a paid generation on air yet.**
The target subscription's `Microsoft.CognitiveServices/Fal.EnableDeploy` feature
was `NotRegistered` at capture time. No model was deployed, no request was sent,
and no third-party terms were accepted. The manifest is `unavailable` for live
generation and recordings, while the educational visual is ready.

![Source-based model options, not generated samples](../../public/demos/fal-video/comparison.svg)

## Presenter path

1. Show `public/demos/fal-video/comparison.svg` from the presentation.
2. Ask: **When is a fast draft more useful than a higher-quality render?**
3. Compare Fast/Pro within LTX and Turbo/Max within MiniMax using the same
   settings within each family. The bars show illustrative cost, not latency.
4. Explain the live gate: access, offering/region, quota, cost, and terms.
   Being in a public-preview announcement does not establish subscription access.

Fast drafts can answer a composition or motion question before committing to a
final render. That is a workflow recommendation, not a measured quality result.
The runner's shared prompt depicts an empty, calm developer desk at dawn with
gentle steam and a slow camera push. It excludes people, readable text, and brands.

## Official evidence and prices

Retrieved **2026-11-09**, approximately **00:40 PST**.

- [Nov 5 Microsoft announcement](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/building-the-next-generation-of-multimodal-ai-experiences-with-fal-in-microsoft-/4570032).
  It is on Tech Community, **not** `devblogs.microsoft.com/foundry`.
  The supplied read-only devblog clone did not contain it.
- [Microsoft Learn: enable, deploy, APIs, settings, quota, and terms](https://learn.microsoft.com/azure/foundry/how-to/fal-ai-models/enable-fal-models).
  This is the model-specific official guide for all five options.
- [Foundry model catalog](https://ai.azure.com). Review the selected model card
  and pricing in an authenticated project after registration; deployment IDs
  cannot be inferred from public display names.
- [Kling public schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kling-video/v3/pro/text-to-video).
  It confirms string duration and `generate_audio`; use Foundry Entra auth,
  not the fal platform's key auth.
- Public fal gallery routes matching Learn's LTX/MiniMax routes returned 404
  during retrieval. Do not treat those pages as verified model cards.

**Pricing has a material unit discrepancy:** the launch prose says USD per
minute, but its table heading says **Price per video second (USD)**. The examples
below multiply the **table** rate by requested seconds. They are illustrative,
not confirmed charges. The launch says prices will reach the Azure pricing page
in the coming weeks. Confirm both the current rate and unit in the deployment
UI before populating the runner's price configuration.

| Model | Official offering / hosting statement | Launch table USD/video-second | Small illustrative request | Access here |
|---|---|---|---|---|
| Kling v3 Pro | US Data Zone; launch says US-hosted | Audio off 0.1232; on 0.1848; audio + voice control 0.2156 | 5 s, audio off: $0.616 | Feature unregistered |
| LTX-2.5 Fast | Global Standard PayGo; launch says initial portfolio US-hosted | 720p 0.09; 1080p 0.13; 1440p 0.19; 4K 0.30 | 720p, 24 fps, 6 s: $0.54 | Feature unregistered |
| LTX-2.5 Pro | Global Standard PayGo; launch says initial portfolio US-hosted | 720p 0.12; 1080p 0.17 | 720p, 24 fps, 6 s: $0.72 | Feature unregistered |
| MiniMax H3 Max | Global Standard PayGo; launch says initial portfolio US-hosted | 480P 0.05; 768P 0.08; 1080P 0.16 | 480P, 5 s: $0.25 | Feature unregistered |
| MiniMax H3 Max Turbo | Global Standard PayGo; launch says initial portfolio US-hosted | 480P 0.025; 768P 0.04; 1080P 0.08 | 480P, 5 s: $0.125 | Feature unregistered |

Learn calls these LTX **v2.5**, while the announcement uses **LTX-2.5**.
The full Turbo name is **MiniMax H3 Max Turbo**.

Kling accepts 3-15 seconds; its public schema does not specify output resolution
or fps. LTX starts at **6**, not 5 seconds. Fast supports higher resolutions and
longer clips, subject to resolution/fps limits; Pro tops out at 10 seconds.
MiniMax supports 0.92-15 seconds, defaults to 768P/5 seconds, and can produce
about 0.7 seconds more than requested. Its 1080P output uses latent refinement
from 768P. Only MiniMax H3 Max adds reference-to-video. Both LTX variants support
synchronized audio. Refer to Learn for all limits.

Learn lists the same RPM tiers for all five: **free 0; tiers 1-4 2; tiers 5-7 40**.
These are documented limits, not verified subscription quota. East US 2 usage
returned no matching fal entry. East US and East US 2 management-plane model
lists returned no matching video model with registration disabled. This does
**not** establish global catalog absence or supported Azure deployment regions.

## Current access evidence (read-only)

Use an explicit subscription argument; do not change the CLI's global default.

```powershell
$sub = az account list --query "[?name=='foundry-devx-sub (nbrady)'].id | [0]" -o tsv
az feature show --namespace Microsoft.CognitiveServices --name Fal.EnableDeploy --subscription $sub --query properties.state -o tsv
az cognitiveservices model list --location eastus --subscription $sub -o json
az cognitiveservices model list --location eastus2 --subscription $sub -o json
az cognitiveservices usage list --location eastus2 --subscription $sub -o json
```

Observed state: **NotRegistered**. No registration command is included.
Microsoft Learn says enabling requires an administrator to review fal terms.
It also says fal services operate outside Microsoft facilities and Microsoft's
customer agreements, DPA, and certifications do not apply. Hosting location
alone does not establish compliance. No organizational or private data was sent.

## Live prerequisites and exact steps (after administrator review)

The runner is implemented and locally tested, but **live API integration is
unverified**. It does not enable a preview feature or create deployments.

### Portable environment contract

The illustration and evidence are static public files and need **no cloud
credentials or environment values**. The runner reads server-side process
environment first, then `demos/fal-video/.env`, then the presentation root `.env`.
Earlier values win. It never exposes credentials through a frontend or `VITE_`
variables. The deck's root example can include the same names below.

| Name | Default | Meaning / blocker |
|---|---|---|
| `FOUNDRY_RESOURCE_ENDPOINT` | Unset | HTTPS `https://<resource>.services.ai.azure.com` root, not a project or fal platform endpoint |
| `FAL_ACCESS_CONFIRMED` | False | Operator confirmation after administrator terms review, feature registration, access and deployment verification; does not itself grant access |
| `FAL_DEPLOYMENTS` | `{}` | JSON map of runner model slugs to exact deployed names; blank/missing model is unavailable |
| `FAL_PRICES_PER_SECOND_USD` | `{}` | JSON map of slugs to positive, independently confirmed USD/video-second rates at the runner settings; missing rate blocks before a paid request |

Auth uses `DefaultAzureCredential` with scope
`https://cognitiveservices.azure.com/.default`. For a local clone, Azure CLI
sign-in is the intended path; managed identity and the normal Azure Identity
environment credentials are also supported. No key is required by this runner.
Keep any Azure Identity secrets only in the server environment or gitignored
dotenv files. Additional blockers are missing `ffprobe`, HTTP access failures,
quota/rate limits, and a failed or timed-out remote generation.

### Setup and run

1. An authorized administrator reviews the Learn acknowledgment and fal terms
   and completes feature registration in the Azure portal. Learn says enabling
   can take up to 30 minutes. This demo does not accept terms on anyone's behalf.
2. In a supported offering/region, create a dedicated Foundry resource/project,
   tagged `handoff=2026-11-09`. Use only newly created resources for any RBAC.
   The administrator needs Subscription Owner/Contributor to enable the feature;
   deployment requires Foundry Owner on the project.
3. Use the Foundry catalog's **Deploy** flow for the chosen model. Verify its
   version, offering, pricing unit/rate, quota and `Succeeded` status. Record the
   exact deployment name. Do not reuse fal platform credentials or deployments.
4. Install Python 3.12+, `uv`, Azure CLI, and `ffprobe` from a trusted FFmpeg
   installation. Sign in to the intended Azure identity. The code follows the
   agent-factory house pattern with `DefaultAzureCredential`, but uses the
   documented REST video API rather than the agent Responses client. No shared
   agent-factory code is vendored or modified.
5. From `weekly-brief/2026-11-06`, copy `demos/fal-video/.env.example` to
   `demos/fal-video/.env` (gitignored), or set the same values in the presentation
   root `.env`. Set the resource endpoint, exact deployment
   mapping and **independently confirmed** price mapping. Set
   `FAL_ACCESS_CONFIRMED=true` only after access is established.
6. Run:

```powershell
uv run demos/fal-video/run.py --json
uv run demos/fal-video/run.py --json --model ltx-2.5-pro
uv run demos/fal-video/run.py --json --model minimax-h3-max-turbo --prompt "A plain notebook on an empty desk at dawn, gentle steam, slow camera push. No people, readable text, logos or brands."
```

If uv cannot reach the normal feed, set a **command-scoped** fallback:

```powershell
$env:UV_DEFAULT_INDEX = "https://packagefeedproxy.microsoft.io/pypi/simple"
uv run demos/fal-video/run.py --json
```

The default prefers configured LTX Fast, then MiniMax Turbo, then the other
variants. No model is empirically fastest here. The runner sends one request,
polls up to 15 minutes, downloads the real result to the gitignored
`public/demos/fal-video/live/`, measures dimensions/duration/fps/file size with
ffprobe, and prints one JSON object. `seconds` includes submission, queue,
generation, download, and probing. Cost is a requested-duration estimate at the
configured price, not an invoice. Errors have `ok:false`, null output metrics,
and exit code 1; **no recording fallback exists**.

API route caveat: Learn's route list omits `/v1`, but its executable examples
include it. The runner follows those versioned examples. Check the deployed
model's current code sample before a first live attempt. Poll failures and
timeouts can leave a remote billed job running; inspect before resubmitting.
Azure bearer tokens are never sent to third-party storage links or redirects.

## Assets, validation, resources and cleanup

`manifest.json` and `evidence.json` are under `public/demos/fal-video/`.
`comparison.svg` is an authored infographic, **not** model-generated media.
No sample video or fake poster is included. Recorded video payload is **0 MB**.
There are no measured timings, fps, clip sizes, or billed clip costs.

Run local contract tests without paid inference:

```powershell
uv run --with azure-identity --with httpx --with python-dotenv python -m unittest discover -s demos/fal-video -p "test_*.py"
```

**Created Azure resources: none. Cleanup commands: none required.**
Nothing existing was modified or deleted. If resources are later created for the
show, leave them in place, record their names here, and delete only the exact
new resource group after presenter approval:

```powershell
# Template only: replace with the exact NEW group after show approval.
az group delete --name <new-handoff-fal-resource-group> --subscription <target-subscription> --yes
```
