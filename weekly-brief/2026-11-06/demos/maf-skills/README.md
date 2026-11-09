# Agent Framework builder skill

This demo shows a coding agent using Microsoft's Python builder skill to create
a small Foundry-backed Agent Framework app. The skill is **development-time
guidance** for the coding agent. It is not a Python dependency and is not
loaded by the shipped app. The separate .NET skill provides language-specific
guidance for .NET developers.

The original generated source is `generated_app.py`. `run.py` uses its
generated `add` function and the same agent configuration, while recording
actual tool calls for the deck. It never substitutes recorded data for a live
failure. The capture in `public/demos/maf-skills/` is available without Azure
credentials.

## Reproduce the build

Source: [Microsoft's Nov 4 guide](https://devblogs.microsoft.com/agent-framework/give-your-coding-agent-a-head-start-with-microsoft-agent-framework-skills-for-net-and-python/),
retrieved November 9, 2026. The guide's `@main` is mutable; this capture used
commit `924a6e50ec0336f3c965ee8b1151c54085888b6e`. Review the skill before
installing and running it. GitHub CLI skill management is preview.

In an **isolated empty Git repository**, not a global skill directory:

```powershell
gh skill preview microsoft/agent-framework agent-framework-builder-python@main
gh skill install microsoft/agent-framework agent-framework-builder-python@main --agent github-copilot --scope project
copilot -p "Use the installed agent-framework-builder-python skill to build a small Python Agent Framework app with a Microsoft Foundry model and one function tool. Use uv, token credentials, and a short runnable example." --trust-folder --allow-tool write --allow-tool 'shell(uv:*)' --deny-tool 'shell(git:*)' --disable-builtin-mcps --no-ask-user --no-color --output-format json
```

The installer placed the skill under `.agents/skills/` in that scratch
repository. Copilot loaded the skill and read `references/agent-builder.md`.
Its output used `Agent`, `FoundryChatClient`, `AzureCliCredential`, and a
local `add` function. This is one run, not a comparative benchmark.

## Run live

Requires Python 3.11+, `uv`, Azure CLI, a Foundry project and a deployed model
supporting function calls, and an Azure identity with inference access.
Sign in using `az login`. Copy the names from `.env.example` to the deck's
`weekly-brief/2026-11-06/.env` file and supply your own project endpoint and
deployment name. Environment variables take precedence over `.env`. Neither
setting has a live default. Keep `.env` local; do not expose credentials to
client-side code. For production, select an appropriate workload credential.

From `weekly-brief/2026-11-06`:

```powershell
uv run demos/maf-skills/run.py --json
```

The script loads `.env` on the server side, runs one agent turn, and
returns a JSON object with the prompt, output, actual function calls, latency
and deployment name. Model requests can incur charges. It exits nonzero if
configuration, authentication, inference, or tool execution fails.
The first run installs the pinned direct dependencies in uv's script
environment. If the normal index is unavailable, use
`$env:UV_DEFAULT_INDEX = "https://packagefeedproxy.microsoft.io/pypi/simple"`.

The captured live run used an existing project and `gpt-5.4-mini` in East US 2.
No Azure resources, agent definitions, deployments, or role assignments were
created, so there is no cloud resource cleanup. The tool has no side effects
and the app sets `store=False` for the model conversation.
