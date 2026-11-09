# Decisions and agent OBO

Present the 28-slide deck, or run the Python examples directly.
Keep this folder intact: the deck adapter imports both sibling Python demos.

## Install

From the repository root, use Python 3.13, `uv`, and Node.js 22.12 or later:

```powershell
Set-Location decisions
uv venv --python 3.13 .venv
uv pip install --python .venv\Scripts\python.exe `
  --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  -r demos\livestream-updates\requirements.txt `
  -r demos\agent-obo-tools\requirements.txt
Set-Location demos\livestream-updates
npm ci --registry=https://packagefeedproxy.microsoft.io/npm/
Set-Location ..\..
```

## Present the slides

For slides without cloud calls, start only Slidev:

```powershell
# From decisions\
Set-Location demos\livestream-updates
npm run dev
```

Open <http://127.0.0.1:3030>. Presenter notes:
<http://127.0.0.1:3030/presenter>. The static deck has no Python backend;
live controls report the missing backend. It does not silently replay fixtures.
Some teaching images and local receiving inputs are explicitly synthetic.

For interactive live panels, copy the **deck-specific** environment file:

```powershell
# From decisions\
Copy-Item demos\livestream-updates\.env.example demos\livestream-updates\.env
# Edit the new .env, then run in terminal 1:
.\.venv\Scripts\python.exe -X utf8 demos\livestream-updates\demo_server.py
# In terminal 2, run Slidev as above.
```

Set `AZURE_OPENAI_ENDPOINT` to the Azure OpenAI resource root, not a project
URL or `/openai/v1` URL. Set `DECISIONS_DEPLOYMENT` to your compatible deployment.
Set `SLIDEV_ENABLE_LIVE=1` after configuration. Model calls can incur Azure costs.

For model authentication, choose one:

- Leave `AZURE_OPENAI_API_KEY` blank and sign in with `az login`. The account
  needs the required Azure OpenAI resource access.
- Set `AZURE_OPENAI_API_KEY` to your resource key. A nonempty key takes
  precedence; a failed key call does not fall back to Entra.

Optional Microsoft-Decision-1 uses `SYSTEMONE_ENDPOINT`, `SYSTEMONE_DEPLOYMENT`,
and `SYSTEMONE_API_KEY`. Its contract differs from Decisions.
An absent `SYSTEMONE_API_KEY` inherits the OpenAI key; an explicitly empty value
selects Entra. See the [deck guide](demos/livestream-updates/README.md).

Python editor execution is a separate opt-in:
`SLIDEV_ENABLE_CODE_RUN=1`. It runs code with your local account's access.
Use trusted code only. Ports 3030 and 8765 bind to loopback; do not expose them
through public tunnels. Stop both terminals with Ctrl+C.

## Run the Python example

These commands run offline using labeled mock answers. They do not prove cloud
authentication, delegated access, latency, or model quality.

```powershell
# From decisions\
.\.venv\Scripts\python.exe -X utf8 demos\decisions-api\decisions_factory.py --mock --step predicate
.\.venv\Scripts\python.exe -X utf8 demos\agent-obo-tools\agent_obo_factory.py --mock
.\.venv\Scripts\python.exe -X utf8 demos\agent-obo-tools\obo_client.py --mock
```

`-X utf8` keeps the examples' Unicode output portable on Windows consoles.

For direct live Decisions calls, copy
`demos\decisions-api\.env.example` to `demos\decisions-api\.env`,
fill your resource endpoint, deployment, and chosen authentication, then remove
`--mock`. The CLI loads `.env` beside its script, regardless of your working
directory. The deck instead loads `demos\livestream-updates\.env`; configure
that file separately. Process environment values take precedence in the CLIs;
the deck's own `.env` overrides inherited values.

## Optional OBO setup

Copy `demos\agent-obo-tools\.env.example` to
`demos\agent-obo-tools\.env` for direct Python use.
OBO requires delegated Microsoft Entra sign-in, a configured client app,
agent blueprint, downstream tool connection, and user/admin consent.
An OpenAI API key cannot replace these.

Required caller values: `TENANT_ID`, `CLIENT_APP_ID`,
`AGENT_BLUEPRINT_CLIENT_ID`, and either `AGENT_OPENAI_BASE_URL` or a valid
`AZURE_AI_PROJECT_ENDPOINT` plus `AGENT_NAME`.
The `.env.example` describes setup-only ARM variables and tool scopes separately.

Review the [OBO setup guide](demos/agent-obo-tools/README.md) before removing
`--mock`. The setup factory creates agent versions and can create connections
and change endpoint authorization; it is not part of the default quickstart.
Do not grant roles or consent without reviewing the scope.

## Validation and limits

```powershell
# From decisions\
Set-Location demos\livestream-updates
..\..\.venv\Scripts\python.exe -m unittest test_demo_server test_catalog_matching test_retail_receiving
npm run build
```

The source owner verified a real Entra Decisions response. This exported copy
is validated offline; API-key authentication and OBO have not been verified live
here. Synthetic examples are not production decisions or access-control checks.
