---
theme: default
title: "Give the model a place to work."
author: Nick Brady
info: |
  Microsoft Copilot harness in Microsoft Foundry.
  Developer livestream. Preview capabilities; sources checked 2 November 2026.
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

<div class="display">Give the model<br>a place to work.</div>
<p class="lede">Microsoft Copilot harness in Microsoft Foundry.<br>From an answer to a checked artifact.</p>
<p class="caption">Prompt agents · tools · skills · workspaces · code-first harnesses</p>

<!--
1 minute. Lead with the outcome: an answer is not the same as a checked notebook.
The Copilot harness is a documented preview. The closing Fusion experiment is
separate, undocumented and unsupported. Do not mix the two claims.
-->

---

# A model is not the whole agent.

<div class="split">
<div class="rule"><h2>The model decides</h2><p>What to say.<br>Which tool to request.<br>When to stop.</p></div>
<div class="rule"><h2>The harness makes it work</h2><p>Runs the loop.<br>Executes tools.<br>Manages context and files.<br>Applies runtime policy.</p></div>
</div>
<p class="lede">The same model can do more when the surrounding system can act.</p>

<!--
2 minutes. A harness is the runtime around a model: tool execution, loop control,
context, state, policy, and observability. Not every harness offers every
capability. This is a general definition, not a claim that the managed preview
lets the user replace all these internals.
-->

---

# The harness closes the loop.

<HarnessOrbit :active="$slidev.nav.currentPage === 3" />

<!--
This illustrative harness checks configured policy and limits, checkpoints state and assesses progress at each shown turn boundary; progress permits a bounded second turn, but only satisfied completion criteria permit the response. A policy block, no progress or exhausted limits is a stop, not successful completion. This is a designed control sequence, not live telemetry or a claim that every SDK, Copilot or Foundry deployment provides these checks or persistence automatically.
-->

---

# Choose who owns the runtime.

| | Default prompt agent | Copilot harness prompt agent | Hosted agent |
|---|---|---|---|
| Runtime owner | Foundry | Foundry | You |
| Invocation | Responses | Responses + conversation | Implemented protocol |
| Workspace / shell | Not in our baseline | Managed built-ins | You wire them |
| Reusable skills | Not in our baseline | Versioned Foundry skills | You load them |
| Custom loop / middleware | Managed | Managed | Your code |

<p class="caption">Default prompt agents can use configured tools. Our baseline deliberately has none.</p>

<!--
2 minutes. Avoid the false claim that default agents cannot use tools.
The baseline here is a plain prompt with no declared tools. Copilot adds a managed
loop and built-ins without us shipping harness code. Hosted gives control but
requires implementation and operations.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness
-->

---
class: chapter
---

<div class="display">Start in the portal.</div>
<p class="lede">A new prompt agent.<br>A different managed runtime.</p>

<!--
30 seconds. Switch to the presenter's existing signed-in Edge window.
Do not show tenant or subscription identifiers on stream.
-->

---
class: demo-slide
---

# Create it. Inspect it. Ask it.

<AgentWalkthrough kind="portal" />

<!--
4 minutes. Live portal demo: New Foundry, gpt-live-project, Create an agent.
Use a NEW name, Text mode, enable Use the Microsoft Copilot harness, Create.
Choose gpt-6-luna. Show Tools > Harness tools: filesystem read/write, shell,
web URL fetching, subagents. Add cookbook-review. Save and start new chat.
Wait for the new active version. Ask a small task, then inspect the trace.
The harness choice is immutable for this agent during preview.
If portal fails, say so and continue to the recorded comparison; this runbook
does not pretend to be a portal recording.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness?pivots=portal
-->

---
class: demo-slide
---

# The same deployment, from azd.

<AgentWalkthrough kind="cli" />

<!--
4 minutes. Show the real terminal in the demo folder. Enable the alpha environment
variable in this shell. Use the already initialized existing-project scaffold.
Show harness.type in azure.yaml, then azd deploy, azd ai agent show --output json.
Confirm kind prompt and microsoft_copilot_preview. Invoke with --new-conversation.
Open the same agent in the portal playground and invoke there.
Do not run azd up against an unreviewed manifest or deploy a new model.
PROJECT_ID comes from a local environment variable; do not print it on stream.
azd 1.37+ and azure.ai.agents beta.22+ required by current Learn.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness?pivots=azd
-->

---

# Small definition. Big runtime change.

```yaml
services:
  recipe-copilot:
    host: azure.ai.agent
    kind: prompt
    model: gpt-6-luna
    harness:
      type: microsoft_copilot_preview
    skills:
      - cookbook-review
    uses:
      - live-project
      - cookbook-review
```

<p class="caption">Keep the generated project fields. Declare the skill as a sibling service.<br><code>skills</code> attaches it. <code>uses</code> orders deployment.</p>

<!--
2 minutes. This is an excerpt, not a complete manifest. The full azure.yaml is
in the demo folder. Publishing a skill creates an immutable version referenced
by the agent version. Changing a skill does not rewrite an old agent version.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
-->

---

# Same API family. Different constraints.

<div class="split">
<div class="rule"><h2>Always a conversation</h2><p>Create one. Send its ID on every request. Reuse it for the next turn.</p><p>Each conversation has its own workspace.</p></div>
<div class="rule"><h2>Not every Responses field</h2><p>No <code>previous_response_id</code>.<br>No <code>store: false</code>.<br>No <code>temperature</code> or structured text format.</p><p>Unsupported fields return errors.</p></div>
</div>
<p class="caption">Reasoning + tool-calling model required. BYOM and Foundry Memory are not supported in this preview.</p>

<!--
2 minutes. Do not copy generic Responses examples blindly. Also omit
max_output_tokens and tool_choice. The conversation is both history and the
workspace key, not a customer-owned durable storage service. Persist outputs.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness
-->

---
class: chapter
---

<div class="display">Don't just write<br>the recipe.</div>
<p class="lede">Build it. Check it. Review it.<br>Give me the notebook.</p>

<!--
1 minute. Introduce Forgebook Recipe Factory as the motivating authoring
environment: recipe-author, cookbook-review, annotated-screenshot, Microsoft
Learn/Foundry/Playwright/GitHub MCP servers. Today's demo is a bounded slice,
not the full upstream publishing workflow.
-->

---

# One task. Two prompt agents.

<div class="split">
<div class="rule"><h2>Same input</h2><p>Teach Entra-authenticated Responses.<br>6–10 notebook cells.<br>Eleven-axis review, 105 points.<br>No notebook model execution.</p></div>
<div class="rule"><h2>Different ability to act</h2><p>Baseline returns text.<br>Harness writes files, runs checks,<br>loads a skill, delegates review,<br>and returns an artifact.</p></div>
</div>
<p class="caption">Use the same compatible deployment for a live comparison. Tool permissions are not identical. Bundled replay is synthetic.</p>

<!--
2 minutes. Show shared-task.md. Its prompt is unchanged across all four author
implementations. Structural and syntax checks do not prove an Azure call ran.
The source README says ten axes; the current review skill has eleven, totaling
105 points. We use the current skill. A Publish verdict is blocked without
reproducible evidence even if the arithmetic is high.
-->

---
class: demo-slide
---

# Same model. From text to an artifact.

<RecipeCompare />

<!--
6 minutes. Synthetic offline mode is selected initially. It is not a service recording.
For an explicitly configured live run, select Live and wait for background authentication.
Run both. The fixed shared prompt is sent unchanged to a fresh conversation in
each agent. Calls run in series for the shared model quota. Point to elapsed time,
streamed tool events and text, token usage, result, code, JSON and cost tabs.
If no price is configured, cost is explicitly unavailable, not zero.
An estimate at token rates excludes any separately metered tools.
Do not claim every built-in ran merely because it was enabled. Inspect actual
events and the portal trace. Download the notebook and review. Show clean cells,
syntax-only validation, and whether the review was independent or self-review.
Quota failures can visibly wait and continue the same conversation twice.
The usage note discloses missing failed-attempt usage. Other failures stay
visible. Bundled fixtures contain no measured latency, token usage, tool calls,
or generated files. The source rehearsal encountered notebook upload failures
and a run with zero downloadable file IDs; do not promise file return.
-->

---

# Tools act. Skills guide. Files persist the work.

<div class="split">
<div class="rule"><h2>Harness built-ins</h2><p>Read / write workspace files.<br>Execute shell checks.<br>Fetch a source URL.<br>Delegate to a subagent.</p></div>
<div class="rule"><h2>A published review skill</h2><p>Reusable review instructions.<br>Immutable version on the agent.<br>Explicit checks and blockers.<br>Notebook + review for download.</p></div>
</div>
<p class="caption">Workspace state is not durable output storage. Downloadable files need agent-identity access to Foundry Files.</p>

<!--
2 minutes. The Web built-in fetches URLs; it is not Foundry web search.
Shell is a broad capability: disabling file/web tools with shell still enabled
is not a strict security boundary. File return uses the agent identity, not
the user's existing role. The new demo agent has a narrowly approved project
role assignment, with cleanup metadata kept off slides.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness#return-generated-files
-->

---
class: chapter
---

<div class="display">When you need<br>to own the loop.</div>
<p class="lede">Copilot SDK hosted agent.<br>Then a custom Agent Framework harness.</p>

<!--
30 seconds. The next demonstrations are code-first. Greater control means more
runtime code, dependency management, error handling and lifecycle ownership.
-->

---
class: demo-slide
---

# Managed harness. Code-first Copilot.

<HostedCompare focus="sdk" />

<!--
4 minutes. Left: managed prompt agent definition and skill. Right: Copilot SDK
hosted agent runtime code, dependencies, auth, lifecycle and hosting. Both author
the identical notebook task. The SDK runtime gives control over tool policy
and application integration; it adds code and operational responsibility.
This export includes synthetic fixtures only. The hosted runner and deployment
are absent. Do not present this slide as evidence of hosted inference.
-->

---
class: demo-slide
---

# Own the loop with Agent Framework.

<HostedCompare focus="maf" />

<!--
4 minutes. Explain the Agent Framework pattern. Its tools, reviewer handoff,
workspace, validation gate and failure policy are application code. Compare to
the SDK runtime. This export includes neither hosted runtime nor deployment.
The synthetic interface is not live or recorded inference evidence.
Custom does not automatically mean more capable; it means
you own the decisions and must implement and operate the capabilities.
-->

---

# Pick the least runtime you need.

| Need | Start here |
|---|---|
| Answer from instructions and configured tools | Default prompt agent |
| Managed multi-step work with files, shell and skills | Copilot harness prompt agent |
| Copilot SDK behavior inside your application runtime | SDK hosted agent |
| Own orchestration, policies and process model | Custom framework harness |

<p class="lede">More control is useful.<br>Unneeded control is work.</p>

<!--
1 minute. No winner for all workloads. Start with the smallest runtime that
satisfies requirements. Validate supported regions/models/tools before a demo
or production design. The Copilot harness remains preview.
-->

---
class: chapter
---

<div class="display">One more thing.</div>
<p class="lede">An experiment, not an announcement.</p>
<span class="badge">UNDOCUMENTED · UNSUPPORTED</span>

<!--
30 seconds. Explicitly separate this experiment from documented Microsoft
Foundry Copilot harness preview. This verified demo uses a local bridge to
GitHub inference; it is not proof of a Foundry-hosted Fusion deployment.
Do not promise availability, SLA, support, or a stable public contract.
-->

---
class: demo-slide
---

# What if a Responses call reached Fusion?

<div class="rule"><h2>Not included in this portable export</h2><p>The experimental Fusion backend is a separate dependency.<br>This slide makes no calls and shows no simulated result.<br>Use the supported recipe comparison on slide 12.</p></div>

<!--
3 minutes. Native live-first Fusion component. DeepSWE opens with Mashumaro
explicitly presenter-selected. Public task prompt only: no repository, no test
execution, NOT GRADED. Test names are held out of model input. Pick another is
an explicit new random live request, not an automatic retry. Random tasks can
hit the retained deadline; show the error honestly. Easy / Hard remains available.
The separate loopback adapter must be ready on 3091; no iframe is used. Easy streams genuine text deltas.
Hard reports actual SDK routing/phase evidence; tools and MCP are denied.
The RECORDED checkbox is an explicit fallback, off by default. No browser token,
secret, tenant or subscription ID belongs in the component or slide source.
Invite interest in the concept, not reliance on an unsupported endpoint.
-->

---

# Keep the artifact. Know the boundary.

<div class="split">
<div class="rule"><h2>Documented preview</h2><p>Copilot harness prompt agents.<br>Managed tools and skills.<br>Conversation-scoped workspace.</p></div>
<div class="rule"><h2>Experimental finale</h2><p>Fusion via Responses.<br>Undocumented and unsupported.<br>No product commitment implied.</p></div>
</div>
<p class="lede">A harness turns model capability into repeatable work.</p>

<!--
1 minute. Close with the notebook, not a feature list.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/use-tools-skills-copilot-harness
Source: https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions#microsoft-copilot-harness-preview
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
-->
