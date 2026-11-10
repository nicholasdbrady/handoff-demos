---
theme: default
title: "The Handoff: weekly Foundry news brief"
author: Nick Brady
info: |
  Microsoft Foundry developer briefing for Nov 09.
  Reporting window: Oct 30 to Nov 06.
class: chapter
colorSchema: auto
aspectRatio: 16/9
canvasWidth: 1280
transition: fade
fonts:
  sans: IBM Plex Sans
  mono: IBM Plex Mono
  provider: none
drawings:
  enabled: false
record: false
download: false
mcp: false
selectable: true
---

<div class="display">The Handoff.<br>Weekly Foundry brief.</div>
<p class="lede">A more complete path from agent code<br>to a result we can verify.</p>
<div class="brief-window"><strong>Oct 30</strong><span>through</span><strong>Nov 06</strong></div>

<!--
I am covering the reporting window from October 30 at 1:01 p.m. Pacific Daylight Time through November 6 at 12:01 p.m. Pacific Standard Time. That precise boundary matters because daylight saving time ended during this week. I will keep product releases, preview models, implementation guidance, and research separate. For developers, the useful question is what changes the next build, test, or deployment decision. Our demos identify captured and live results explicitly. Where our environment cannot run a model, the diagrams and walkthroughs still explain how it works, the developer tradeoff, and the prerequisites for trying it.

Sources, reporting window supplied by editorial brief; announcements dated 2026-11-05 and 2026-11-06, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/improve-production-agents-with-closed-loop-evaluations-in-microsoft-foundry/4569762
https://commandline.microsoft.com/thinkingbox-part-two-expanded-model-evals-reinforcement-learning-rewards/
-->

---

# Four threads. One developer workflow.

<div class="brief-quad">
<div><h2>Build and inspect agents</h2><p>Configuration, tools, skills, deployment.</p></div>
<div><h2>Code on local hardware</h2><p>Cache once. Check hardware fit.</p></div>
<div><h2>Choose a new model</h2><p>Video drafts and long-context work.</p></div>
<div><h2>Verify the final state</h2><p>Outcomes, regression checks, repeatability.</p></div>
</div>

<!--
I see four connected threads rather than nine unrelated announcements. First, the agent development workflow is becoming more complete, from reviewed configuration to inspection and deployment. Second, local coding is practical only when the model and execution provider fit the hardware. Third, the model portfolio adds video and very large context windows, with preview and availability boundaries that we must respect. Fourth, the research and improvement guidance ask us to check actual outcomes. These are my synthesis of the week, not four new product launches. I will use the visuals to connect each announcement to a developer decision.

Sources, 2026-11-05/06, checked 2026-11-09:
https://github.com/microsoft/Foundry-Local/releases/tag/v2.3.0
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292
https://commandline.microsoft.com/thinkingbox-part-two-expanded-model-evals-reinforcement-learning-rewards/
-->

---

# 1. From agent code to reviewed configuration.

<div class="brief-status"><span class="badge">Foundry azd bundle · 1.0</span><span class="badge">GA</span></div>
<div class="brief-flow">
<div><h2>Agent code</h2><p>Build the application.</p></div><span aria-hidden="true">→</span>
<div><h2>azure.yaml</h2><p>Review deployment intent.</p></div><span aria-hidden="true">→</span>
<div><h2>Agent Inspector</h2><p>Test locally.</p></div><span aria-hidden="true">→</span>
<div><h2>Hosted agent</h2><p>Deploy to Foundry.</p></div>
</div>

<!--
I am starting with the development workflow: agent code, a reviewed azure.yaml, local Agent Inspector testing, and deployment to a hosted agent. The value is not simply another CLI command. It is keeping deployment intent next to the application so that another engineer can review it before infrastructure changes. The bundle's 1.0 announcement is the GA milestone; individual capabilities can have their own lifecycle. A full deployment still requires Azure permissions, quota, azd 1.37 or later, and billable resources. I will return to this workflow in our first show-ready conversation and show the actual demo state separately.

Sources, announcement 2026-11-05, checked 2026-11-09:
https://devblogs.microsoft.com/foundry/microsoft-foundry-azure-developer-cli-ga/
https://github.com/Azure/azure-dev/tree/main/cli/azd/extensions/azure.ai.agents
-->

---

# 2. Local coding starts with hardware fit.

<div class="brief-status"><span class="badge">SDK 2.3.0</span><span class="badge">CLI 0.13.0 · preview</span></div>
<svg class="brief-diagram" viewBox="0 0 1100 240" role="img" aria-label="Python, .NET and Java SDKs reuse a shared model cache which feeds local inference">
<rect x="10" y="50" width="230" height="130" rx="12"/><text x="125" y="110">SDK clients</text><text class="brief-svg-caption" x="125" y="146">Python · .NET · Java</text>
<path d="M240 115h150m-15-10 15 10-15 10"/>
<rect x="390" y="50" width="300" height="130" rx="12"/><text x="540" y="110">Shared model cache</text><text class="brief-svg-caption" x="540" y="146">Reuse downloaded models</text>
<path d="M690 115h150m-15-10 15 10-15 10"/>
<rect x="840" y="50" width="250" height="130" rx="12"/><text x="965" y="110">Local inference</text><text class="brief-svg-caption" x="965" y="146">Execution provider + GPU</text>
</svg>
<p class="caption">Qwen walkthrough: ~18 GB model · NVIDIA ≥24 GB VRAM · separate CUDA + cuDNN setup</p>

<!--
I want us to separate the SDK update from the hardware decision. Foundry Local SDK 2.3.0 adds a shared native model cache and inference and reliability improvements. CLI 0.13.0 is still preview. The Qwen coding walkthrough is a specific setup, not a minimum requirement for every Foundry Local model: its package is approximately 18 gigabytes and the example needs an NVIDIA GPU with at least 24 gigabytes of VRAM, plus CUDA and cuDNN setup. Our hardware does not meet that example, so I am using the architecture visual to explain model sharing and hardware fit. Local inference also does not make all surrounding Copilot operations offline.

Sources, releases 2026-11-02/05, checked 2026-11-09:
https://github.com/microsoft/Foundry-Local/releases/tag/v2.3.0
https://github.com/microsoft/Foundry-Local/releases/tag/cli-preview-0.13.0
https://devblogs.microsoft.com/foundry/foundry-local-agentic-coding-qwen3-8-27b/
-->

---

# 3. Video: draft quickly, then choose quality.

<div class="brief-status"><span class="badge">fal in Foundry · public preview</span><span class="badge">Initial portfolio hosted in the US</span></div>
<table class="brief-models">
<thead><tr><th>Model family</th><th>Fast draft option</th><th>Quality-oriented option</th></tr></thead>
<tbody>
<tr><td>LTX-2.5</td><td>Fast</td><td>Pro</td></tr>
<tr><td>MiniMax H3</td><td>Max Turbo</td><td>Max</td></tr>
<tr><td>Kling v3</td><td>Compare on your prompt</td><td>Pro</td></tr>
</tbody>
</table>

<!--
I am treating model selection as a workflow decision: when do I need a fast draft, and when is another quality pass worth the time and cost? Microsoft announced five fal portfolio models in public preview: Kling v3 Pro, LTX-2.5 Fast and Pro, and MiniMax H3 Max and Max Turbo. The brief's shorthand Turbo name needs the full Max Turbo product name. The initial portfolio is US-hosted; the announcement lists Kling as US Data Zone and LTX and MiniMax as Global Standard. This table is a conceptual comparison. Later I will show five generated clips, each with its own prompt; different briefs make them examples, not a controlled comparison.

Source, 2026-11-05, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/building-the-next-generation-of-multimodal-ai-experiences-with-fal-in-microsoft-/4570032
-->

---

# 4. A million-token workspace for context.

<ContextScale />

<!--
I am showing scale rather than promising that more tokens automatically produce better answers. Kimi K3.1 Pro is open weight, accepts text and images, and provides roughly one million tokens of context. The November 5 announcement establishes its arrival. The current catalog and Learn lifecycle table, checked November 9, label version 2026-11-04 GA; I am not claiming an archived catalog label at the reporting cutoff. Developers still need to check input limits, region, cost, and whether the model uses the relevant evidence. The shorter reference bars illustrate scale. Our bounded document check is not a million-token capacity benchmark.

Source, 2026-11-05, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292
https://ai.azure.com/catalog/models/Kimi-K3.1-Pro (current catalog checked 2026-11-09)
https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule#foundry-models-sold-by-azure (version 2026-11-04 listed GA, checked 2026-11-09)
-->

---
class: demo-slide
---

# Kimi: build a three.js scene.

<KimiComparison />

<!--
I sent the identical kinetic-sculpture prompt at none, low, and high reasoning effort, with a twelve-thousand completion-token cap. The generated three.js documents are unedited; our wrapper provides the pinned runtime and an isolated frame, not code repairs. These captured calls used 4,833, 6,263, and 10,965 total tokens and took 18.78, 32.55, and 62.33 seconds. Reasoning tokens are included in output tokens, not an additional charge category. I will switch the setting, pause the scene, reset its view, and reveal the exact shared prompt. One sample per setting shows the work performed; it does not establish a causal quality ranking.

Source, 2026-11-05, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292
Capture measurements: 2026-11-09T09:00:40.715333Z; public/demos/kimi-k3-1-pro/manifest.json and recorded-results.json.
-->

---
class: benchmark-slide
---

# Kimi: test a harder task.

<DemoCapture class="capture-benchmark" slug="kimi-k3-1-pro-benchmark" asset-match="benchmark.html" />

<!--
I asked Kimi to read an image policy, select a route, join distributed records while rejecting stale epochs, and verify real SDK code facts. Each high-effort trial received 373,132 service-reported input tokens. All three attempted trials passed, with all thirty-three exact fields correct. Latencies were 37.3, 26.6, and 25.0 seconds; the median was 26.6 seconds. The uncached cost estimate totals about two dollars sixty, not a billing receipt. The source code is real; the planted routing records are fictional fixtures. This is a small bespoke benchmark, not a leaderboard or a million-token test. I can expand the exact prompt and grading.

Source, model announcement 2026-11-05, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292
Captured 2026-11-09T09:21:08.106280Z; public/demos/kimi-k3-1-pro-benchmark/manifest.json and recorded-results.json.
-->

---

# 5. Builder skills guide the coding agent.

<svg class="brief-diagram" viewBox="0 0 1100 240" role="img" aria-label="Development-time builder skills guide Copilot to produce an Agent Framework application; runtime skills are separately configured">
<rect x="10" y="35" width="300" height="160" rx="12"/><text x="160" y="100">Builder skills</text><text class="brief-svg-caption" x="160" y="140">.NET + Python guidance</text>
<path d="M310 115h90m-15-10 15 10-15 10"/>
<rect x="400" y="35" width="270" height="160" rx="12"/><text x="535" y="100">Coding agent</text><text class="brief-svg-caption" x="535" y="140">Builds + checks your app</text>
<path d="M670 115h90m-15-10 15 10-15 10"/>
<rect x="760" y="35" width="330" height="160" rx="12"/><text x="925" y="100">Shipped application</text><text class="brief-svg-caption" x="925" y="140">Runtime skills are separate</text>
</svg>

<!--
I want to make this boundary unmistakable. Agent Framework builder skills guide a coding agent while it develops a .NET or Python application. They help it choose patterns and load the relevant framework guidance. The November 4 guide recommends the smallest suitable pattern and pairing focused builder guidance with Microsoft Learn MCP for complete documentation. These skills are not automatically runtime skills inside the application it ships, and the Python builder skill is not a Python package installed by that application. For developers, this avoids confusing the assistant's development instructions with the deployed agent's capabilities. Pin the skill revision when you need a reproducible development environment.

Sources, guide 2026-11-04, checked 2026-11-09:
https://devblogs.microsoft.com/agent-framework/give-your-coding-agent-a-head-start-with-microsoft-agent-framework-skills-for-net-and-python/
https://learn.microsoft.com/agent-framework/get-started/build-with-coding-agents
https://learn.microsoft.com/agent-framework/agents/skills
-->

---
class: demo-slide
---

# Builder skills: from guidance to checked code.

<DemoCapture slug="maf-skills" />

<!--
I will follow the coding agent from the builder instructions into the application it produces. The captured Python application called the add tool once with nineteen and twenty-three, then returned forty-two. Its measured live run took 10.602 seconds. I can inspect the installed guidance, generated code, and execution transcript separately. The skill helps the coding assistant choose framework patterns and checks; it is not imported by the shipped application. The application configures its own Foundry client, instructions, and function tool. For developers, that gives us two review boundaries: check the assistant's development work, then check what the deployed application actually does.

Sources, guide 2026-11-04, checked 2026-11-09:
https://devblogs.microsoft.com/agent-framework/give-your-coding-agent-a-head-start-with-microsoft-agent-framework-skills-for-net-and-python/
https://learn.microsoft.com/agent-framework/get-started/build-with-coding-agents
https://github.com/microsoft/agent-framework/tree/main/skills
-->

---

# 6. Improve the agent. Gate the promotion.

<ImprovementLoop />

<!--
I am presenting an implementation pattern, not a turnkey product launch. The production loop starts with traces and human-reviewed outcomes, tests tools in isolation, and evaluates a candidate against held-out regression cases before canary promotion. Agent Optimizer is preview. The guidance connects optimization to engineer review rather than granting the optimizer authority to ship its own changes. Developers should keep training and validation separate from the held-out release gate and measure production outcomes after the canary. The animation illustrates those boundaries; it is not live telemetry. The important change is making evidence and release controls part of one repeatable improvement process.

Source, 2026-11-06, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/improve-production-agents-with-closed-loop-evaluations-in-microsoft-foundry/4569762
-->

---

# 7. Three useful Toolkit checks.

<div class="brief-status"><span class="badge">Foundry Toolkit for VS Code · 1.6.19</span></div>
<div class="brief-cards">
<div><h2>Connect</h2><p>Project-connection models in builders and playgrounds.</p></div>
<div><h2>Inspect policy</h2><p>Findings before model deployment.</p></div>
<div><h2>Watch the build</h2><p>Hosted-agent container progress in Output.</p></div>
</div>

<!--
I am focusing on the three Toolkit 1.6.19 changes that reduce friction while building. Project-connection models become available in Agent Builder, hosted-agent creation, and Model Playground. Policy findings appear in model details and before deployment, giving developers a chance to inspect governance constraints earlier. Audit findings are non-blocking; that does not make every policy effect advisory. Hosted-agent container build progress is visible in the Toolkit Output channel, which makes waiting easier to diagnose. The release also contains other improvements, but these cards isolate one useful story: discover the right model, inspect the deployment conditions, and observe the build.

Sources, release 2026-11-04, checked 2026-11-09:
https://microsoft.github.io/foundry-dev-tools/
https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio
-->

---

# 8. Foundry Canvas keeps the agent in reach.

<div class="brief-cards">
<div><h2>Choose a harness</h2><p>Prompt agents with harness.<br><span class="badge">Preview</span></p></div>
<div><h2>Start from a prompt</h2><p>Agent prompt gallery.</p></div>
<div><h2>Refresh resources</h2><p>Models, tools, toolboxes, skills.</p></div>
</div>

<!--
I am separating recently documented features from the version synchronization record. Foundry Canvas notes describe prompt agents with harness in preview, an agent prompt gallery, and resource refresh for models, tools, toolboxes, and skills. Those features make the Copilot-side workflow more practical without turning a version number into a feature announcement. The plugin repository has a 1.0.19 sync record, but the detailed published changelog does not yet provide a 1.0.19 feature section. I will not assign undocumented changes to that version. For developers, use the available feature notes to understand behavior and the sync record only to identify the plugin version.

Sources, recent notes and sync checked 2026-11-09:
https://github.com/microsoft/foundry-dev-tools/blob/main/microsoft-foundry/changelog.md
https://github.com/microsoft/foundry-dev-tools/tree/main/microsoft-foundry
https://github.com/microsoft/foundry-dev-tools/commit/bba484bffc275cc9640f61b7b7357be0f943e16b (1.0.19 sync, 2026-11-05T07:06:01Z)
https://devblogs.microsoft.com/foundry/microsoft-copilot-harness-in-foundry/ (2026-10-28 preview announcement; pre-window context)
-->

---

# 9. "Done" is a claim. State is evidence.

<VerifiedState />

<!--
I am using a deliberately illustrative interaction to show why a completion message is weaker than checking the resulting state. ThinkingBox evaluates executable tasks in stateful environments. In this research, reinforcement learning on tasks outside the benchmark increased the number of tasks passed on every one of twenty attempts from thirty-eight to one hundred seven out of five hundred seven. That is a research-trained Qwen checkpoint, not a claim about the stock local model. Passing twenty recorded attempts also does not guarantee attempt twenty-one. For developers, the lesson is to verify the artifact or business record and measure repeatability, not merely collect a convincing transcript.

Source, 2026-11-06, checked 2026-11-09:
https://commandline.microsoft.com/thinkingbox-part-two-expanded-model-evals-reinforcement-learning-rewards/
-->

---

# Migration: check the runtime and deployment.

<div class="brief-migrations">
<div><section><h2>Agent Framework</h2><span class="badge">Python 1.24.0</span></section><p>Supported baseline: Python 3.11+.<br>3.10 can install, but is unsupported.<br>Beta Redis: rebuild legacy indexes and re-ingest.</p></div>
<div><section><h2>Foundry azd agents</h2><span class="badge">Extension 1.0</span></section><p>A bare image no longer suppresses registry provisioning.<br>Developer RBAC warnings are opt-in.<br>Role checks and automatic assignment stay enabled.</p></div>
</div>

<!--
I am grouping the changes that can alter an existing environment. Agent Framework Python 1.24.0 supports Python 3.11 and later; installability on 3.10 is not a support commitment. The beta Redis provider rejects legacy indexes, so I would schedule a controlled index rebuild and re-ingestion rather than discover it during a production request. In the azd agents extension, supplying a bare image no longer prevents registry provisioning. Developer RBAC warnings become opt-in, but role checks and automatic role assignment remain enabled. Developers should review their existing deployment configurations and permissions before upgrading, especially when their automation assumes previous provisioning behavior.

Sources, release notes checked 2026-11-09:
https://github.com/microsoft/agent-framework/releases/tag/python-1.24.0
https://github.com/Azure/azure-dev/blob/main/cli/azd/extensions/azure.ai.agents/CHANGELOG.md
-->

---

# Migration: update the client contract.

<div class="brief-migrations">
<div><section><h2>Python Projects</h2><span class="badge">2.10.0</span></section><p>Simulation-seed generation exposes service-required <code>max_samples</code>.</p></div>
<div><section><h2>.NET betas</h2></section><p>Review required <code>maxSamples</code> in Projects.<br>Use <code>BrowserAutomationToolboxTool</code> instead of the preview-named toolbox type.</p></div>
<div><section><h2>REST specifications</h2></section><p>OpenAPI + voice-schema update merged Nov 04.</p></div>
</div>

<!--
I am treating these as client-contract migration notes, not a service rollout announcement. Python azure-ai-projects 2.10.0 exposes the service-required max_samples field for simulation-seed generation and updates the sample to pass it directly. For .NET beta users, the current Projects and Agents changelogs are the upgrade authority: review the required sample-count parameter and the replacement BrowserAutomationToolboxTool name. An unreleased changelog entry must not be described as a shipped package. Finally, the November 4 OpenAPI and voice-schema merge is evidence of a specification update only. Developers must separately confirm that the endpoint, model, and region they intend to call are available.

Sources, changelogs/specification checked 2026-11-09:
https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md
https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/ai/Azure.AI.Projects/CHANGELOG.md
https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/ai/Azure.AI.Projects.Agents/CHANGELOG.md
https://github.com/Azure/azure-rest-api-specs/tree/main/specification/ai-foundry
https://github.com/Azure/azure-rest-api-specs/pull/47288 (merged 2026-11-04T03:45:45Z)
https://github.com/Azure/azure-rest-api-specs/pull/47196 (merged 2026-11-04T19:17:30Z)
-->

---

# A cutoff is not a calendar date.

<div class="brief-window"><strong>Published before cutoff</strong><span>│</span><strong>Oct 30</strong><span>│</span><strong>This week's window</strong></div>
<div class="brief-quad">
<div><h2>JavaScript Projects 2.10.0</h2><p>Already published before the precise boundary.</p></div>
<div><h2>Agent Framework .NET 1.27.0</h2><p>Already published before the precise boundary.</p></div>
</div>

<!--
I am keeping these versions visible because developers may still need the migration context, but I am not counting them as new within this reporting window. JavaScript Projects 2.10.0 and Agent Framework .NET 1.27.0 were published before the precise October 30 cutoff. A date-only release summary can make a same-day package appear new when its publication time falls outside the window. The distinction is editorial, not a judgment about the importance of the release. I would still inspect the changelog before upgrading; I simply will not inflate this week's news count with packages already available at the start.

Sources, package/release records checked 2026-11-09:
https://github.com/Azure/azure-sdk-for-js/releases/tag/%40azure/ai-projects_2.10.0 (published 2026-10-30T17:10:46Z)
https://github.com/microsoft/agent-framework/releases/tag/dotnet-1.27.0 (published 2026-10-30T18:55:48Z)
Reporting cutoff: 2026-10-30T20:01:00Z.
-->

---
class: chapter
---

<div class="display">What belongs<br>in azure.yaml?</div>
<p class="lede">Conversation 1 · From code to hosted agent.</p>
<div class="brief-window"><strong>Code</strong><span>→</span><strong>Reviewed config</strong><span>→</span><strong>Local test</strong><span>→</span><strong>Deploy</strong></div>

<!--
I will ask what we can keep in a reviewed azure.yaml instead of configuring by hand. That question leads naturally to application code, deployment configuration, local Agent Inspector testing, and hosted deployment. I will use the GA walkthrough as the educational path even if our live environment is not ready. Before any real deployment, I need the required permissions, quota, azd 1.37 or later, and an understanding of the billable resources. The demo panel distinguishes captured evidence from live execution. Developers can reuse the review boundary immediately, without assuming that every viewer has the same Azure access or deployment environment.

Sources, announcement 2026-11-05, checked 2026-11-09:
https://devblogs.microsoft.com/foundry/microsoft-foundry-azure-developer-cli-ga/
https://github.com/Azure/azure-dev/tree/main/cli/azd/extensions/azure.ai.agents
-->

---
class: demo-slide
---

# azd: inspect configuration and execution.

<DemoCapture slug="azd-agent" />

<!--
I will start with the reviewed azure.yaml: agent code, project dependency, model version, deployment type, and runtime resources. The recorded Agent Inspector screenshot shows a real local request that took 396.8 seconds; I will show that as recorded evidence, not repeat it as our live path. The captured hosted invocation took about 11.9 seconds. The Run live button makes a new hosted request using our server-side configuration and Azure CLI identity. Source upload and remote build avoid requiring a local container build. For developers, configuration review, local inspection, and hosted execution are distinct checks; none substitutes for the others.

Sources, workflow checked 2026-11-09:
https://github.com/Azure/azure-dev/tree/main/cli/azd/extensions/azure.ai.agents
https://devblogs.microsoft.com/foundry/microsoft-foundry-azure-developer-cli-ga/
-->

---
class: chapter
---

<div class="display">Which coding tasks<br>fit your hardware?</div>
<p class="lede">Conversation 2 · Local coding with Copilot.</p>
<div class="brief-window"><strong>Model size</strong><span>→</span><strong>GPU + provider</strong><span>→</span><strong>Task + verification</strong></div>

<!--
I will use the Qwen walkthrough to discuss which coding tasks are practical on a developer's own hardware. I am not running this example on our machine because its hardware requirements exceed what we have. The example uses an approximately eighteen-gigabyte model and an NVIDIA GPU with at least twenty-four gigabytes of VRAM; CUDA and cuDNN require separate setup. Those are example-specific constraints, not a blanket requirement for every local model. Local inference describes where model execution happens, not whether every surrounding Copilot operation is offline. Developers should check the execution provider, memory fit, network boundaries, and code-validation path before selecting this workflow.

Sources, Local releases checked 2026-11-09:
https://github.com/microsoft/Foundry-Local/releases/tag/v2.3.0
https://github.com/microsoft/Foundry-Local/releases/tag/cli-preview-0.13.0
https://devblogs.microsoft.com/foundry/foundry-local-agentic-coding-qwen3-8-27b/
-->

---
class: chapter
---

<div class="display">When is a draft<br>more useful?</div>
<p class="lede">Conversation 3 · Video model choice.</p>
<div class="brief-window"><strong>Creative brief</strong><span>→</span><strong>Model choice</strong><span>→</span><strong>Evaluate output</strong></div>

<!--
I will discuss when a fast draft is more useful than a higher-quality render. A draft can answer composition and direction questions before we pay for a final pass. The fal models are in public preview, with model-specific availability and pricing. We enabled access and deployed all five models in East US 2, then created one clip per model. Each clip uses a different creative brief, so the examples show possible workflows rather than measured differences in speed, quality, or cost. A controlled comparison would need matched prompts and repeated runs.

Source, 2026-11-05, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/building-the-next-generation-of-multimodal-ai-experiences-with-fal-in-microsoft-/4570032
-->

---
class: demo-slide
---

# Choose the right video model.

<DemoCapture slug="fal-video" asset-match=".mp4" clip-label="Microsoft Foundry · fal · public preview" no-live no-metrics />

<!--
These five clips use different briefs, not a ranking. Prompts name subjects and cameras; LTX and H3 include sound or timing cues. Select a model to see its exact prompt. Kling's manta passes a doorway; flooding and bubbles are unclear, the camera follows frontally, and the wings stretch. LTX Fast's marble rolls past rods; chime impacts and vibration are not visible, and the texture shifts. LTX Pro cuts to the same fox; stepping out and looking up are not clear. H3 Max's petals open; three gears are indistinct, the subject drifts, and the final pulse is unconfirmed. Turbo shows a warm desk. LTX and MiniMax contain audio; synchronization was not assessed.

Sources, 2026-11-05; five clips captured 2026-11-09: estimated $2.126 for the four new clips plus $0.125 for Turbo, total $2.251; Azure Monitor cost metrics were empty and no invoice was available.
Request IDs: Kling 06f64fca-2ef2-4fcc-a677-2630af739e72; LTX Fast 740643d2-7598-42db-84c2-9f045bcf7cfa; LTX Pro 839f265e-599c-444b-aaa5-a77c48ce5f7c; H3 Max e9476e3d-41e9-428a-bfd4-ab13a026a85d. The Turbo request ID was not captured.
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/building-the-next-generation-of-multimodal-ai-experiences-with-fal-in-microsoft-/4570032
https://blog.fal.ai/kling-3-0-prompting-guide/
https://fal.ai/learn/tools/how-to-use-ltx-2-5
https://fal.ai/learn/tools/how-to-use-minimax-h3-max
-->

---

# MAI Image 2.6: check the deployment status.

<div class="brief-cards">
<div><h2>Oct 27</h2><p>Announcement:<br>2.6 + Flash called GA.</p></div>
<div><h2>Nov 05</h2><p>October roundup:<br>2.6 called preview.</p></div>
<div><h2>Learn guide</h2><p>Older guidance:<br>both listed as preview.</p></div>
</div>

<!--
I am preserving the status conflict instead of smoothing it into a more confident story. The October 27 announcement calls MAI Image 2.6 and Flash generally available. The November 5 October roundup describes 2.6 as preview, while the older Microsoft Learn deployment guide labels both as preview. Those statements do not establish a new GA milestone or a downgrade during this reporting week. For developers, the decision point is the actual deployment's current status, supported region, and applicable terms. I would confirm those before making a production recommendation. This is useful context about inconsistent public labels, not another ranked launch.

Sources, 2026-10-27/2026-11-05 and older Learn guide, checked 2026-11-09:
https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-october-2026/
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/mai-image-2-6-and-mai-image-2-6-flash-are-now-generally-available-in-microsoft-f/4566327
https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image
-->

---

# A roundup is a reference, not this week's launch list.

<div class="brief-quad">
<div><h2>Useful on screen</h2><p>October Foundry roundup.<br>Ignite session list.</p></div>
<div><h2>Keep the boundary</h2><p>October launches are not new this week.</p></div>
<div><h2>RSS was empty</h2><p>Microsoft AI discovery coverage was limited.</p></div>
<div><h2>Sitemap is not proof</h2><p>No newly dated MAI announcement found in the window.</p></div>
</div>

<!--
I will keep the October roundup available as an on-screen reference, especially its Ignite session list. Its publication this week does not move October launches into this week's reporting window. The Microsoft AI RSS feed was empty, and its public sitemap did not reveal a newly dated MAI model announcement in this window. That describes the coverage of those discovery channels, not proof that no other announcement exists. Developers should use the roundup to find sessions and revisit relevant capabilities, while keeping launch dates and model status grounded in the direct sources. I am separating useful navigation from claims of completeness.

Sources, roundup 2026-11-05; RSS/sitemap coverage supplied by editorial brief, checked 2026-11-09:
https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-october-2026/
https://microsoft.ai/
-->

---
class: chapter
---

<div class="display">Build it.<br>Inspect it.<br>Verify the outcome.</div>
<p class="lede">Reviewed configuration. Hardware fit.<br>Model choice. Evidence before promotion.</p>

<!--
I will close with one developer habit: make the next boundary observable. Put deployment intent in reviewed configuration. Check hardware fit before choosing a local coding model. Select video and long-context models according to the task, availability, preview status, and cost. Use builder guidance to improve development without confusing it with runtime capabilities. Finally, verify the resulting artifact or business state and gate improvement on held-out checks. The week's research does not guarantee that an agent succeeds, but it strengthens the case for measuring real completion. Our demo panels keep missing, captured, and live evidence separate so that the show follows that same standard.

Sources, 2026-11-05/06, checked 2026-11-09:
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/improve-production-agents-with-closed-loop-evaluations-in-microsoft-foundry/4569762
https://commandline.microsoft.com/thinkingbox-part-two-expanded-model-evals-reinforcement-learning-rewards/
-->
