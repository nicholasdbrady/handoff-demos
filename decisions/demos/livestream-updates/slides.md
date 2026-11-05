---
theme: default
title: "Decide on evidence. Act with the user."
author: Nick Brady
info: |
  Azure OpenAI Decisions API and agent on-behalf-of-user tool connections.
  Developer livestream, 27 October 2026. Sources checked 27 October 2026.
class: dark-slide
colorSchema: auto
aspectRatio: 16/9
canvasWidth: 1280
transition: fade
fonts:
  sans: Manrope Variable
  provider: none
drawings:
  enabled: false
record: false
download: false
mcp: false
selectable: true
---

<div class="display">Decide on evidence.<br>Act with the user.</div>

<p class="lede">Two developer updates in Microsoft Foundry.<br>Live demos you can run from these slides.</p>

<div class="title-pair">
<div><h2>Azure OpenAI Decisions API</h2><p>Typed answers for application decisions.</p></div>
<div><h2>Agent on-behalf-of-user</h2><p>User + agent identity at the tool boundary.</p></div>
</div>

<!--
~1 minute. Start with the practical difference, not an announcement list.
The first update changes what a model returns. The second changes which
identity reaches a tool. These are separate capabilities, not one combined API.
Inference controls call the live service. The retail extraction and exact
checks use labeled synthetic fixtures; only its optional semantic step calls a model.
-->

---

# What's new

<div class="split">
<div class="rule">
<h2>A dedicated decision endpoint</h2>
<p>Evaluate text or images as predicates, choices, or ordered scores.</p>
<p class="accent"><code>/openai/v1/decisions</code></p>
<p class="caption">Requires a <code>gpt-6-luna</code> deployment in a supported region.</p>
</div>
<div class="rule">
<h2>An agent can be the OBO actor</h2>
<p>A downstream token represents both the signed-in user and the agent identity.</p>
<p class="accent"><code>AgentOnBehalfOfUser</code></p>
<p class="caption">Preview. Direct runtime clients, blueprint-audience sign-in, and tool-specific consent.</p>
</div>
</div>

<!--
~1 minute. Describe these as documented updates. The Decisions article was
updated October 23; the user-delegation documentation also shows an October 23
update. A documentation timestamp is not evidence of the initial announcement
date. We have not verified a separate public announcement post for Agent OBO.
Do not claim that OBO was first announced this week.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Source: https://learn.microsoft.com/azure/foundry/agents/concepts/user-delegation
-->

---
class: demo-slide
---

# System 1 and System 2 on the same ticket.

<SystemCompare />

<!--
~3 minutes. Both lanes call the same gpt-6-luna deployment with the same three
questions as the first code slide. Run from the main slide window.
Left: one Decisions request. Typed answers, distributions, zero output tokens.
Right: the Responses API with reasoning effort high and a reasoning summary.
It thinks first, then writes an answer and reasons in text.
Select Run both. Watch the two clocks, then compare output shape and tokens.
Try Mixed signals: System 2 explains the trade-off; System 1 gives numbers
to branch on.
Each clock shows one live run from this machine. Time varies with network,
load, and input. Do not present it as a benchmark or a universal speedup.
Measured 26 October on Mixed signals: Decisions 0.6-4.4 s (median 1.4 s,
23 calls) with 0 output tokens; Responses 2.3-3.9 s with 70-171 reasoning
tokens. The token gap is consistent. The time gap is not: System 1 can finish
second. If it does, say so, then lead with output shape and tokens.
The thinking box is a model-written summary, not the full chain of thought.
Summaries are best effort. If the box says no summary, point to the
reasoning-token count instead.
Cost under each clock: an estimate per 1K runs from this run's tokens at the
Azure list price for gpt-6-luna, Global Standard. Measured 26 October on
Mixed signals: about $0.05 for System 1 and $0.11-0.12 for System 2; System 2
moves with reasoning tokens. Decisions has no separate
published price, so say "estimate at token rates". Hover for one run.
Code tab: the exact Python call each lane sends for this ticket. Change the
preset to show the request change. No Azure call.
JSON tab: after Run both, the raw response bodies. Point to typed answers and
usage on the left; output items and reasoning tokens on the right.
Framing credit: TypeSafe and Kahneman, as on the previous slide.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning
-->

---

# What a decision model is—and is not.

<div class="split">
<div class="rule">
<h2>It is</h2>
<ul class="ledger">
<li><strong>A function call</strong><span>Input and typed questions in. Typed answers out.</span></li>
<li><strong>A fixed answer space</strong><span>A predicate, one of your choices, or an ordered score.</span></li>
<li><strong>One pass</strong><span>Each question sees the same input on its own.</span></li>
<li><strong>Classify, route, and prioritize</strong><span>Typed judgments for repeated application checks.</span></li>
</ul>
</div>
<div class="rule">
<h2 class="accent">It is not</h2>
<ul class="ledger">
<li><strong>A chat model</strong><span>No conversation. No generated text.</span></li>
<li><strong>A multi-step reasoner</strong><span>Split the judgment into questions. Combine in code.</span></li>
<li><strong>A tool caller or agent</strong><span>It answers. Your application acts.</span></li>
<li><strong>An authority</strong><span>A probability is evidence, not a guarantee.</span></li>
</ul>
</div>
</div>

<!--
~2 minutes. Framing credit: TypeSafe's "System One" concept page explains
this class of model well, and the name comes from Daniel Kahneman's
"Thinking, Fast and Slow". System 1 and System 2 are a framing for this talk,
not Azure product names.
It is: state plus typed questions in, typed answers with probabilities out,
like calling a function. The answer space is fixed by you: a predicate returns
a probability from zero to one, a choice returns one of your values, a score
returns a position on your ordered levels. Questions do not see each other's
answers.
It is not: a chat model, a multi-step reasoner, or a tool caller. If question
B needs the answer to question A, make a second request or combine the
answers in code. Learn routes your own JSON schemas, written explanations,
and tool calls to the Responses API.
A probability is not permission: escalate refusals and low confidence.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Framing: https://docs.typesafe.ai/concepts/system-one
-->

---
class: demo-slide code-slide
clicks: 1
---

# One call. Three answer shapes.

<CodeRunStatus />

<div class="demo code-stage-switch" @click.stop @keydown.stop>
<div class="view-switch" role="group" aria-label="Code walkthrough">
<button :aria-pressed="$clicks === 0" @click="$clicksContext.current = 0">One predicate</button>
<button :aria-pressed="$clicks > 0" @click="$clicksContext.current = 1">Three answer shapes</button>
</div>
</div>

<div v-if="$clicks === 0">

```python {monaco-run} {autorun:false, ata:false, height:'508px'}
decision = client.decisions.create(
    model=DEPLOYMENT,
    input="I was charged twice. Please return the extra charge.",
    questions=[
        {
            "name": "wants_refund",
            "type": "predicate",
            "instructions": "Does the customer ask for money back?",
        },
    ],
)

print(decision.answers[0].model_dump_json(indent=2))
print("input tokens:", decision.usage.input_tokens)
```

</div>
<div v-else>

```python {monaco-run} {autorun:false, ata:false, height:'508px'}
teams = ["billing", "technical", "security", "other"]
levels = ["none", "low", "medium", "high", "critical"]

decision = client.decisions.create(
    model=DEPLOYMENT,
    input="Every PDF export fails since 2.14. Month-end close is tomorrow.",
    questions=[
        {"type": "predicate", "name": "wants_refund",
         "instructions": "Does the customer ask for money back?"},
        {"type": "choice", "name": "team",
         "instructions": "Which team should own this ticket?",
         "choices": [{"value": t} for t in teams]},
        {"type": "score", "name": "severity",
         "instructions": "How severe is the business impact?",
         "levels": [{"label": l} for l in levels]},
    ],
)

for answer in decision.answers:
    print(answer.model_dump_json(indent=2))
```

</div>

<!--
Start with One predicate. The local runner supplies client and DEPLOYMENT.
Run, then select Three answer shapes. Both examples are editable and runnable.
Only Run calls Azure; switching examples does not.
Point to predicate probability, choice and its allowed values, and zero-based score levels.
Five levels give a 0-to-4 scale; a fractional weighted score is expected.
Named questions share input but do not see each other's answers.
Use the typed answer object, handle refusal, and do not parse generated prose.
The runner owns authentication; no secret is in the slide.
Presenter-view editors are separate copies; run from the main slide window.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
-->

---
class: demo-slide
---

# Turn answers into a route.

<DecisionDemo />

<!--
~4 minutes. Each Run sends the
ticket to your Azure resource.
Run Duplicate charge. Point to billing, then the severity score and predicates.
Move the threshold: the policy changes without another model call.
Try Account takeover, then General feedback to show human review.
All six questions share one input; these are not six dependent reasoning steps.
The panel suggests a route. It takes no refund, account, or paging action.
Flow: Vue controls -> local Python adapter -> existing Decisions demo.
-->

---

# The uncertain path is part of the design.

<div class="split">
<div>
<h2>Keep the policy in your code.</h2>
<p>Refused or missing answer?<br><strong>Human review.</strong></p>
<p>Low confidence or “other”?<br><strong>Human review.</strong></p>
<p>Threshold passed?<br><strong>A suggested route, not authority.</strong></p>
</div>
<div>

```python
for answer in decision.answers:
    if answer.type == "refusal":
        queue_for_review(answer.name)
    elif answer.type == "predicate":
        evaluate_policy(
            probability=answer.probability
        )
```

<p class="caption" style="margin-top: 24px">Tune thresholds on labeled examples and the cost of each error. Probability and choice/score confidence are different signals, not accuracy guarantees.</p>
</div>
</div>

<!--
~2 minutes. Any answer can be a refusal; do not access probability or score
until checking its type. A refusal may have no name.
The example functions are application pseudocode, not SDK methods.
Application policy owns the action.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions#interpret-answers-and-handle-refusals
-->

---
class: demo-slide suitcase-slide
---

# Inspect the suitcase. Then change the trip.

<ImageDecisionDemo />

<!--
This is the gpt-6-luna Decisions route, not Microsoft-Decision-1.
The fixtures are original AI-generated photorealistic images, not copied assets.
Start with Sunshine kit. Ask viewers: rain protection? footwear? clear view?
Then run. Switch to Rain kit, then Under cover. These are teaching inputs,
not an evaluation dataset. Synthetic pictures do not establish accuracy.
Input contains only an input_image part. The question instructions define
rain protection, footwear category, and evidence quality.
Select Python to show local file -> base64 data URL -> input_image.
Select JSON after Run to show distributions and any refusal.
A low presence probability on an obscured image is not proof of absence.
Look at the distributions and confidence; handle refusals.
The model sees PNG pixels, not fixture names, generation prompts, or expected answers.
Only the Run button calls the model. The same key/Entra client is reused.
Select Add a trip brief on this same page. The selected suitcase stays fixed.
Keep Sunshine kit selected. Start with Beach weekend.
Ask the audience to vote: Ready, Repack, or Need a closer look? Then run.
Select Plot twist: rain. The pixels do not change. Run again.
An editable trip brief joins the image in shared input. A fourth, independent
score question evaluates fit: mismatch 0, partial 1, suited 2.
Expected contrast: the sunshine equipment suits the beach more than a cold,
muddy festival. This is a hypothesis, not a guaranteed answer. Report real output.
Try Rain kit, then Under cover. Hidden equipment must not become "missing".
All questions see the same image and text. None sees another question's answer.
Code, not the model, applies the example rule: clear evidence plus quality and
fit confidences >=0.65; fit >=1.5 means Ready, otherwise Repack.
Missing answers, any refusal, obscured evidence, or low confidence mean review.
These are illustrative thresholds, not calibrated safety guarantees.
The Python view includes the exact routing function. No autonomous action occurs.
Business analogy: suitcase + trip brief becomes packing photo + order requirements
or technician kit + work order. Exact quantities and arithmetic belong in code.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
-->

---
class: demo-slide retail-slide
---

# From a packing slip to a receiving exception.

<RetailReceivingDemo />

<!--
Generic retail scenario, not a Target-specific policy or customer implementation.
The packing slip and extracted fields are synthetic teaching fixtures, not a live DI/CU response.
Start with Clear source. Code validates OCR confidence, field confidence, source regions,
units/currency, parsing, and consistency. It computes 12 - 10 = 2 cases and 2 * USD18.50 = USD37.00.
That is a reference value, never a payable supplier claim.
Only select Route note with Luna to make a live semantic request. The note says
"Two held at depot; send with next delivery." A choice interprets partial delivery, damage, or other.
Quality failures stop the call. Try low OCR confidence, missing region, and contradictory quantities.
A high model probability cannot override these gates. A structured reason code skips the model.
OCR recognition confidence, field-extraction confidence, decision probability,
choice confidence, and source geometry are not interchangeable. No universal trust score.
The thresholds 0.9 and 0.8 are illustrative, not calibrated; evaluate on labeled examples.
Native OCR/DI/CU source regions usually remove the need for another box-finding pass.
Use DI prebuilt for an established invoice/receipt schema; CU for varying layouts and semantic fields.
Use Responses structured outputs for custom extraction; Decisions supplies bounded judgments.
No live extraction, OCR benchmark, automatic payment, supplier claim, or service-accuracy claim.
Source: https://learn.microsoft.com/azure/ai-services/content-understanding/choosing-right-ai-tool
Source: https://learn.microsoft.com/azure/ai-services/content-understanding/document/analyzer-improvement
Source: https://learn.microsoft.com/azure/ai-services/document-intelligence/prebuilt/layout
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
-->

---
class: coverage-slide api-contract-slide
---

# Pick the API, not just the model name.

<table class="api-contracts" aria-label="Decision API contracts and SDK support">
<thead><tr><th scope="col">Contract</th><th scope="col">Azure OpenAI Decisions</th><th scope="col">Microsoft System One</th></tr></thead>
<tbody>
<tr><th scope="row">Endpoint</th><td><code>/openai/v1/decisions</code></td><td><code>/providers/microsoft/v1/systemone</code></td></tr>
<tr><th scope="row">Request</th><td><code>input</code> + questions array</td><td><code>state</code> + named questions object</td></tr>
<tr><th scope="row">Answer types</th><td><code>predicate</code> · <code>choice</code> · <code>score</code></td><td><code>noul</code> · <code>choice</code> · <code>score</code></td></tr>
<tr><th scope="row">Response</th><td>Answers array</td><td>Named answers object</td></tr>
<tr><th scope="row">SDK / REST</th><td><strong>OpenAI SDKs</strong><small>Python ≥3.26.0 · JavaScript ≥7.30.0<br>REST also works.</small></td><td><strong>TypeSafe SDKs: wire-compatible</strong><small>Python / TypeScript · verified: text + <code>noul</code><br>Microsoft-Decision-1 deployment · or REST.</small></td></tr>
</tbody>
</table>

<!--
System 1/System 2 earlier was a conceptual framing. System One here is an
actual provider API route. The endpoint, input, question, and response schemas
are different. A base URL switch is not sufficient.
The Microsoft route uses criteria objects for choice and ordered arrays for
score. Its binary primitive is called noul, not predicate.
The SDK version floors apply to native OpenAI decisions methods, not generic
HTTP access to Microsoft-Decision-1. TypeSafe SDKs can target this provider's
System One wire format; this is not a dedicated Foundry SDK method.
Live smoke tests on 2026-10-29 succeeded with typesafe-sdk 0.7.5 and
@typesafe-ai/sdk 0.7.0 against our Azure Microsoft-Decision-1 deployment.
Verified scope: text input and a typed noul response, not full feature parity.
Set base_url / baseURL to the resource root plus /providers/microsoft.
Both SDKs append /v1/systemone. Use the deployment name as model / defaultModel,
disable compression, and pass an Entra bearer token via api_key / apiKey.
The short-lived examples do not renew tokens. Images and Box are not verified.
REST remains an alternative from any HTTP-capable language.
The model fields use deployment names in these documented resource routes.
These sources do not establish instant/project-route Decisions support.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Source: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
Source: https://docs.typesafe.ai/introduction
-->

---
class: demo-slide microsoft-slide
---

# Microsoft-Decision-1: the native request.

<MicrosoftDecisionDemo />

<!--
Start on Python, then switch to TypeScript. Both TypeSafe SDK samples use
Entra and a placeholder resource endpoint/deployment. Sign in with az login
and install typesafe-sdk + azure-identity, or @typesafe-ai/sdk + @azure/identity.
The token is passed through the SDK's API-key
parameter as a bearer token; these short-lived examples do not refresh it.
Compression is disabled. Run still sends the same native payload through
the local adapter; the displayed SDK samples are copyable, not an editor runner.
Point to state, named questions, noul, criteria, and the answers object.
Change the ticket to an outage. Only Run sends a model request.
The three questions are independent. The four score levels run from 0 to 3,
unlike the earlier five-level 0-to-4 example.
This optional panel needs a real Microsoft-Decision-1 deployment, specified
by SYSTEMONE_DEPLOYMENT. No resource is provisioned by this deck. If it is not
configured, show the code without claiming a successful live call.
Run opens the visual Response view: noul probability, selected team, and
the fractional severity score on the requested 0-to-3 scale.
The JSON view preserves the actual native response. Do not invent an
explanation field or translate its output into the OpenAI schema.
Source: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
-->

---
class: demo-slide provider-slide
---

# Same product—or a costly mistake?

<ProviderCompare />

<!--
Run 12 pairs starts two independent series: one in-flight request per provider.
Both receive the same original synthetic records and identical matching rubric.
Select rows to show renamed products, different capacities, pack sizes, missing
attributes, and confirmed conflicts. Product photos are decorative, not model input.
Different means a sellable variant conflict, not merely a different marketing name.
Review is a legitimate reference answer when the decisive information is absent.
Equivalent attribute notations such as GB and gigabytes need not mean different products.
Reference labels and reasons are authored separately and never enter inference.
Matches are exact reference-label agreement, not confidence or a general quality benchmark.
Failures, refusals, and invalid answers do not count as matches. Failed items remain visible.
No records are merged and no model failure falls back to synthetic results.
Each main timer measures the full browser batch wait and freezes without replacing it
with backend time. API calls total is a separate sum, not pure model inference time.
Cost per 1K pairs divides the whole batch's usage estimate by 12, then multiplies by 1,000.
Any failed call or unknown cost makes the batch cost unavailable, not zero.
Both providers process the same order with no cross-provider synchronization.
Select Request or JSON to inspect a pair without resetting the running batch.
The small synthetic set illustrates tradeoffs; use repeated representative labeled
workloads before selecting a provider. No winner is precomputed or claimed.
The comparison requires existing configured deployments and provisions nothing.
Inspired by https://docs.typesafe.ai/cookbooks/entity_alignment
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Source: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
-->

---

# A judgment is not permission.

<div class="flow">
<div class="flow-node"><strong>Model judgment</strong><small>Evaluate the evidence.<br>Return typed answers.</small></div>
<span class="arrow"></span>
<div class="flow-node"><strong>Application policy</strong><small>Check quality and thresholds.<br>Suggest a controlled next step.</small></div>
<span class="arrow"></span>
<div class="flow-node"><strong>Service authorization</strong><small>Enforce who can access data.<br>Never trust a model score as permission.</small></div>
</div>

<p class="lede" style="margin-top: 40px">The next boundary is identity:<br>whose permissions does the agent's tool use?</p>

<!--
Close Decisions before moving to Agent OBO. These are separate capabilities.
A decision can suggest a queue, but cannot grant permissions or authorize a refund.
OBO carries scoped user and agent identity; it does not validate the judgment.
The OBO demo is a read-only profile lookup, not a privileged action chained from triage.
-->

---
class: dark-slide
---

<div class="chapter"><div>
<h1>Now the agent<br>needs the user's data.</h1>
<p class="lede">How does the tool know both<br>who the user is and which agent is acting?</p>
</div></div>

<!--
~30 seconds. Transition from a model judgment to an access boundary.
Foundry Agent Service: agent identity as the OBO actor, in preview.
We are not chaining the refund decision into privileged action.
The next demo uses a read-only profile lookup.
-->

---

# Three boundaries. Three separate decisions.

<div class="boundary"><strong>Admin</strong><span class="arrow"></span><strong>Foundry resources</strong><span>Who can create and manage the agent?</span></div>
<div class="boundary"><strong>Caller</strong><span class="arrow"></span><strong>Agent endpoint</strong><span>Who can invoke it, with which audience?</span></div>
<div class="boundary"><strong>Agent</strong><span class="arrow"></span><strong>Downstream tool</strong><span>Which identity reaches the data?</span></div>

<p class="lede" style="margin-top: 38px">Permissions do not carry across these boundaries.</p>

<!--
~2 minutes. Having an Azure role that lets you create an agent does not imply
runtime access. Being able to call the agent does not grant tool permissions.
The downstream service remains the authorization authority.
Management, invocation, and data access are separate.
Source: https://learn.microsoft.com/azure/foundry/agents/concepts/identity-access-overview
-->

---

# Which identity is the OBO actor?

| Connection auth type | Actor selection | Key constraint |
| --- | --- | --- |
| `UserEntraToken` | Foundry or agent, based on the incoming token audience | Limited supported tools |
| `AgentOnBehalfOfUser` | Always the agent identity, on behalf of the user | Blueprint audience required |
| `OAuth2` | Separate per-connection user sign-in | Client must handle the sign-in flow |

<p class="caption" style="margin-top: 32px">Agent-identity OBO is in preview. Tool and channel support differ.<br>Conditional Access and the downstream service's authorization policy still apply.</p>

<!--
~2 minutes. Avoid saying UserEntraToken always means Foundry is the actor.
The incoming audience changes that behavior for supported tools.
AgentOnBehalfOfUser is the explicit agent-only actor configuration.
Verify support for the specific tool.
Do not claim that delegated access eliminates every standing permission an
agent may have through other connections.
Source: https://learn.microsoft.com/azure/foundry/agents/concepts/user-delegation
-->

---

# Configure both sides of the boundary.

<div class="split">
<div>
<h2>Tool connection</h2>

```json
{
  "authType": "AgentOnBehalfOfUser",
  "scopes": [
    "api://<tool-app>/<scope>"
  ]
}
```

<p class="caption" style="margin-top: 20px">Explicit, fully qualified scopes.<br>One downstream resource per connection.</p>
</div>
<div>
<h2>Caller to agent</h2>

```text
Endpoint scheme:
  AgentBlueprint

Caller token scope:
  api://<blueprint-id>/access_agent
```

<p class="caption" style="margin-top: 20px">Authorize the client app and retain every endpoint scheme you still need when patching the array.</p>
</div>
</div>

<!--
~2 minutes. These are configuration excerpts, not full deployment payloads.
Use agent_obo_factory.py for the prepared setup, but verify its preview ARM
API version against your tenant before live use. We do not provision, patch
endpoint permissions, or grant consent from this presentation.
The endpoint patch replaces the array: preserve any existing schemes you need,
not just the two shown in the original new-agent sample.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/configure-user-delegation
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-endpoint-authorization
-->

---

# Consent is a resumable step, not a dead end.

<ol class="step-list">
<li><span>User signs in for the <strong>agent blueprint</strong>.</span></li>
<li><span>Response may contain <code>oauth_consent_request</code>.</span></li>
<li><span>User completes consent in the <strong>product-owned browser flow</strong>.</span></li>
<li><span>Client continues with <code>previous_response_id</code>.</span></li>
<li><span>Tool authorizes the <strong>user + agent</strong> request.</span></li>
</ol>

<!--
~1 minute. Consent can already be satisfied by admin consent or
preauthorization, so a prompt is not guaranteed on every first demo run.
Some tenant policies prohibit user consent. Never imply that Enter grants it.
Consent does not override data permissions.
The app surfaces consent links but does not inspect or relay downstream tokens.
Sign-in and consent cannot be safely forced into a presentation iframe.
Source: https://learn.microsoft.com/azure/foundry/agents/how-to/mcp-authentication
-->

---
class: demo-slide
---

# Call the agent as the user.

<OboDemo />

<!--
~4 minutes. Requires the existing agent, connection, and client app in .env
(see README). Reload the slide after changing the local configuration.
Select Sign in & call agent. Complete Microsoft sign-in in the separate
browser window, off the broadcast. If requested, open every consent link and
finish it before you select I finished consent · continue.
The response stays hidden until you select Reveal response. Reveal only a
test account that is safe for the stream.
Reset clears local state, not Microsoft consent or browser sign-in. Select a
different test account in the next sign-in flow.
The flow calls an existing agent; it never creates cloud resources.
Credentials and continuation IDs stay server-side.
Flow: Vue controls -> local Python adapter -> existing OBO client.
-->

---

# The proof is an access test, not a profile.

| Scenario | Required live evidence |
| --- | --- |
| User A is authorized | A gets only data A can access |
| User B lacks access | B cannot retrieve the protected data |
| Consent is incomplete | The client pauses, then resumes correctly |
| Wrong audience or missing scope | A real failure, with no privileged fallback |

<p class="caption" style="margin-top: 28px">Same agent, separate authenticated user contexts. Review actual tool results and failures.<br>A model saying “I can't access it” does not prove enforcement.</p>

<!--
~1 minute. A profile lookup demonstrates user context, not full isolation.
The protected-data test requires your real tool and two prepared users.
Never reuse user A's token for user B.
Reset clears this demo's in-memory session, not Microsoft browser cookies
or tenant consent. Select the second account during Microsoft's sign-in flow.
No tenant-level isolation claim has been verified by the offline tests.
Source: https://learn.microsoft.com/azure/foundry/agents/concepts/entra-delegated-access-consent
-->

---
class: dark-slide
---

<div class="display">A model judges.<br>Your code decides.<br>The service authorizes.</div>

<p class="lede">Keep those responsibilities separate.</p>

<!--
~30 seconds. The connection between the two updates is architectural:
typed evidence for application decisions, and scoped user context for tool
access. A probability never expands permissions. OBO never validates a model
judgment. Two capabilities, independent boundaries.
-->

---

# Keep the code. Keep the sources.

<div class="split">
<div>
<h2>Build on the demos</h2>
<p><code>demos/decisions-api/</code><br>Typed answers, image input, caching.</p>
<p><code>demos/agent-obo-tools/</code><br>Setup script and delegated runtime client.</p>
<p><code>demos/livestream-updates/</code><br>Markdown slides + Vue + local adapter.</p>
</div>
<div>
<h2>Read the current contract</h2>
<p><a href="https://learn.microsoft.com/azure/foundry/openai/how-to/decisions">Azure OpenAI Decisions API</a></p>
<p><a href="https://learn.microsoft.com/azure/foundry/agents/concepts/identity-access-overview">Foundry identity boundaries</a></p>
<p><a href="https://learn.microsoft.com/azure/foundry/agents/concepts/user-delegation">Agent OBO and consent</a></p>
<p><a href="https://sli.dev/guide/work-with-ai">Slidev skills and MCP authoring</a></p>
</div>
</div>

<!--
~30 seconds. Sources checked 26 October 2026. Preview contracts can change.
Take questions.
For follow-up editing: slides.md changes the story and notes,
components/*.vue changes the interactions, and demo_server.py changes the
server adapter. The official Slidev skill is installed in this workspace.
The installed Slidev CLI also includes `slidev mcp slides.md` for structured
read/edit/reorder tools. The HTTP MCP endpoint is disabled by default here.
-->

---

# Appendix: One input. Many independent questions.

<div class="flow">
<div class="flow-node"><strong>Shared evidence</strong><small>A ticket, a document,<br>or text plus images.</small></div>
<span class="arrow"></span>
<div class="flow-node"><strong>Named questions</strong><small>Up to 400 in a request.<br>Each sees the same input.</small></div>
<span class="arrow"></span>
<div class="flow-node"><strong>Typed answers</strong><small>Match by name.<br>Handle each refusal.</small></div>
</div>

<p class="lede">If question B needs the answer to question A,<br>make a second request.</p>

<!--
~1 minute. Multiple questions amortize shared input evaluation, but they do
not communicate answers to each other. It is not a dependency graph.
Images are supported as HTTPS URLs or base64 data URLs. Use images you have
permission to send and avoid showing personal address labels on a livestream.
The image slides later in this deck show image-only and image-plus-brief
requests. This ticket panel stays text-only.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
-->

---

# Appendix: Measure your workload, not the headline.

<div class="split">
<div class="rule">
<h2>Latency</h2>
<p>Compare equivalent tasks, models, prompts, and output requirements.</p>
<p>Warm both paths. Repeat runs. Report the setup and distribution.</p>
</div>
<div class="rule">
<h2>Caching</h2>
<p>Reuse a stable input prefix and inspect <code>cached_tokens</code>.</p>
<p>A cache key is not a promise of a hit.</p>
</div>
</div>

<p class="caption" style="margin-top: 34px">Responses remains the path for generated text, custom JSON output, and tool calls.</p>

<!--
~1 minute. The System 1 and System 2 clocks are single live runs, not a
benchmark. No universal speedup or pricing claim.
Do not quote the original mock "12x faster" output. Those sleeps were
programmed into a mock and are not a benchmark.
The original CLI cache and latency steps are optional experiments, not the
headline evidence in this deck. Its latency comparison needs equivalent
prompts and warm-ups before it is used for a publishable performance claim.
Avoid applying OpenAI public API pricing to Azure; link Azure's current pricing.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
-->

---
class: coverage-slide
---

# Appendix: One category. Different model surfaces.

| Model / family | Where we verified it | Evidence inputs |
| --- | --- | --- |
| **gpt-6-luna · Decisions** | Azure OpenAI in Microsoft Foundry | Text, images, or both |
| **Microsoft-Decision-1** | Microsoft provider in Foundry | Text or JSON documented |
| **Laya** | Open-source Python / self-hosted HTTP | Text / structured state |
| **Jev · TypeSafe** | TypeSafe; separate Azure Databricks integration | Check the selected provider |

<p class="caption">First two rows: documented Foundry paths. Last two: wider ecosystem,<br>not verified managed Foundry offerings. This is not an exhaustive catalog.</p>

<!--
Decision models are a category, not one SDK method. The Decisions API currently
supports gpt-6-luna. Microsoft-Decision-1 is a separate model and provider route.
Do not pass it to client.decisions.create() just by changing the model name.
Laya belongs to Convai Innovations, not TypeSafe. Its model card documents a
Python package and a self-hosted Jev-compatible /v1/systemone server.
Jev is TypeSafe's model. Its Azure Databricks support is not Foundry support.
We have not verified Laya or Jev as managed Foundry offerings. Do not call this
table the complete catalog. No cross-vendor latency or calibration ranking.
Source: https://learn.microsoft.com/azure/foundry/openai/how-to/decisions
Source: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
Source: https://huggingface.co/convaiinnovations/laya
Source: https://docs.typesafe.ai/introduction
Source: https://learn.microsoft.com/azure/databricks/machine-learning/model-serving/query-systemone-models
-->
