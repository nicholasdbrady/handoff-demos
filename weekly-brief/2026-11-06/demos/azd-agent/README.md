# From code to a hosted agent: Foundry azd 1.0

The complete example is in this repository. `project/` contains the official
basic Python Agent Framework Responses sample, initialized with Foundry azd 1.0.
The reviewed `project/azure.yaml` deploys `handoff-azd-agent` by uploading source
for a remote build. No local Docker build or Azure Container Registry is needed.

## What to show

Open `project/azure.yaml` beside the
[November 5 GA walkthrough](https://devblogs.microsoft.com/foundry/microsoft-foundry-azure-developer-cli-ga/).
Walk through the project dependency, model name and version, deployment SKU and
capacity, Python runtime and entry point, protocol version, and CPU/memory.
These settings move from hand configuration into a reviewed source file.
Subscription, region, and deployment outputs remain environment-specific.
`.azure/` and `.env` are not committed.

The actual sequence was initialization, review, provisioning, a local CLI
invocation and Agent Inspector test in Microsoft Edge, remote deployment, and
remote invocation. Agent version **2** is active. Version 1 failed during the
remote dependency build; both the error and successful retry are captured.

## Run the live demo from this repository

Prerequisites: Python 3.13+, `uv`, Azure CLI, and an Azure CLI login with Foundry
data-plane access to the deployed agent. A provisioning identity also needs
resource creation and role-assignment permission. This example uses
`AzureCliCredential`, not API keys; it follows the agent-factory client pattern
of Entra authentication plus the project's OpenAI client.

From `weekly-brief/2026-11-06`:

```powershell
Copy-Item demos\azd-agent\.env.example demos\azd-agent\.env
# Edit the two values in demos\azd-agent\.env for your own deployment.
uv run demos/azd-agent/run.py --json
```

Required environment contract: inherited process environment takes precedence,
then the deck's `weekly-brief/2026-11-06/.env`, then `demos/azd-agent/.env`.
Paths are resolved relative to this script, not the terminal's working directory.

| Variable | Value |
| --- | --- |
| `AZD_AGENT_PROJECT_ENDPOINT` | Your HTTPS Foundry project endpoint, ending `/api/projects/<project>`; no default |
| `AZD_AGENT_NAME` | Your deployed hosted agent's name; example `handoff-azd-agent` |

The default prompt is a cloud-deployment haiku. Use `--prompt "your prompt"` to
change it. The runner prints one JSON object with `ok`, `prompt`, `output_text`,
`latency_ms`, `agent`, and `endpoint_host`. On failure it adds `error` and exits
nonzero. It requires a completed streamed response and **never replays a capture**.
Hosted agents use their own `/agents/<name>/endpoint/protocols/openai` route,
not the project-level prompt-agent `agent_reference` route.

No credentials enter Slidev/browser code. Do not expose these settings as
`VITE_` variables. The runner has inline uv dependency metadata, so it does not
depend on a checkout of agent-factory or another machine's virtual environment.

## Reproduce the GA walkthrough

Use Azure Developer CLI 1.37+ and `microsoft.foundry`/`azure.ai.agents` 1.0.0.
The capture used azd 1.38.0-beta.1-daily.7005316, uv 0.12.0, local Python 3.14.4,
and a Python 3.13 hosted runtime. Model quota and billable Azure resources are
required. Verify both CLI logins target the same account and tenant.

```powershell
azd extension install microsoft.foundry
# For an older installation:
azd extension update microsoft.foundry

# Use a separate empty directory; do not overwrite the bundled project.
azd ai agent init --src . --no-prompt `
  --template https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/agent-framework/responses/01-basic/azure.yaml `
  --agent-name handoff-azd-agent --deploy-mode code `
  --runtime python_3_13 --entry-point main.py

# Review azure.yaml. Keep the service key and name identical.
azd env set AZURE_SUBSCRIPTION_ID "<your-subscription-id>"
azd env set AZURE_LOCATION northcentralus
azd env set AZURE_RESOURCE_GROUP "<your-new-demo-resource-group>"
azd env set AZURE_AI_PROJECT_NAME "<your-new-project>"
azd provision --no-prompt
```

The bundled file increases the sample's minimum versions to azd 1.37 and
agents 1.0, and aligns the service key with `name: handoff-azd-agent`. The source
and public PyPI lockfile remain the official sample. Provisioning the bundled
project in a fresh checkout can also require `azd env new <your-environment>`.
Supply your subscription/region using the commands above, then provision.

To run locally, restore dependencies in the service directory with `uv sync
--frozen`. Return to the project root and run:

```powershell
azd ai agent run --no-client --port 8098
```

In another terminal in the project directory:

```powershell
azd ai inspector launch --port 8098 --inspector-port 8097
# Open http://localhost:8097 in Microsoft Edge.
azd ai agent invoke --local --port 8098 "Write a haiku about deploying cloud applications."
```

The local model call uses the newly provisioned Foundry deployment. After local
testing, stop the local processes with Ctrl+C. Deploy and invoke:

```powershell
azd deploy --no-prompt
azd ai agent show --output json
azd ai agent invoke "Write a haiku about deploying cloud applications."
```

`azd up --no-prompt` combines package, provision, and deploy. The captured run
uses the split commands so the local check sits before deployment. Evaluation
and CI/CD steps from the article are educational follow-ons, not exercised by
this basic demo.

### Tags and cleanup

The capture created only this new resource group and its resources:

| Resource | Name |
| --- | --- |
| Resource group (North Central US) | `rg-handoff-azd-20261109` |
| Foundry account | `cog-mvrbqcz5lwi26` |
| Foundry project | `handoff-azd-project` |
| Model deployment | `gpt-5.4-mini`, version `2026-03-17`, Global Standard, capacity 10 |
| Hosted agent | `handoff-azd-agent`, active version 2 |

Resource group, account, and project have `handoff=2026-11-09`. Model deployments
and hosted agent versions do not expose the same generic ARM tagging surface.
The azd deployment also creates managed agent identities and the required role
assignments for this new agent. No existing cloud resources were modified.

The environment variable `AZURE_TAGS` did not apply these tags automatically.
After provisioning, this run merged tags only on the newly created resources.
For another reproduction, apply tags explicitly to your new group/account/project.

The deployed agent is left running for the show and incurs Azure charges.
**Do not execute cleanup before the show.** After confirming the CLI subscription
and reviewing the named group, the resource owner can remove this demo:

```powershell
az group show --name rg-handoff-azd-20261109 --query "{name:name,tags:tags}"
az group delete --name rg-handoff-azd-20261109
```

Alternatively, from the original azd project/environment, review `azd down`.
Deletion is not performed by this demo.

## Captured and no-credentials path

Open `../../public/demos/azd-agent/manifest.json` and its assets without Azure
credentials. It includes real initialization/config/provision/deploy/invoke
transcripts, the completed Inspector screenshot, the invocation JSON, and
source-grounded 1.0 notes. Read the screenshot and `walkthrough.json` while
showing the source configuration. Do not call this recorded path a live run.

Important presenter caveats:

- The Inspector request took **396.8 seconds** in this capture; its screenshot
  is a completed real result, not a normal-latency claim. Local CLI took about
  20 seconds and the deployed runner about 12 seconds. Use the recorded Inspector
  image in the show, then the live runner.
- On this corporate network, direct `files.pythonhosted.org` downloads failed
  with TLS `HandshakeFailure`. Local dependencies were restored through
  `https://packagefeedproxy.microsoft.io/pypi/simple`. Do not send that locally
  rewritten lockfile to the remote builder: that build failed. Restoring the
  official sample's public PyPI lockfile fixed the remote build on the next attempt.
  On this network, use a temporary local proxy lock for local development and
  restore the official public lock before remote deployment. The committed
  lockfile is the successful remote-build version.
- GA extension status does not imply that every optional runtime feature is
  enabled. This sample does not exercise resilience, tool approvals, or evaluation.
- The 1.0 registry/RBAC changes are verified from first-party release notes.
  A bare-image registry deployment and deliberately denied RBAC assignment were
  **not** tested; no extra resources were created for those demonstrations.

## What changed in agents 1.0

The [November 5 release notes](https://github.com/Azure/azure-dev/blob/main/cli/azd/extensions/azure.ai.agents/CHANGELOG.md)
state that a bare `image` no longer suppresses registry provisioning. Prebuilt
deployments should set `docker.imagePassthrough: true`, or the supported
`AZD_AGENT_SKIP_ACR=true` with a nonempty image. This code-upload demo does not
need a registry.

Developer RBAC warnings in final/JSON output now require
`AZD_ALPHA_ENABLE_AGENTS_RBAC_WARNINGS=true`. Role checks and automatic role
assignment remain enabled. Turning off warnings is **not** turning off access
checks. Review existing deployment configurations before upgrading.

`capture.ps1` records timed, redacted command output. Review every new capture
before publishing; automatic redaction cannot guarantee the absence of all
possible sensitive values.
