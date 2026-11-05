<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { streamDemo, type LiveResult } from '../demo-stream'
defineProps<{ kind: 'portal' | 'cli' }>()
const step = ref(0)
const ready = ref(false)
const busy = ref(false)
const output = ref('')
const error = ref('')
const resultView = ref('text')
const raw = ref<unknown>()
const result = ref<LiveResult>()
const elapsed = ref(0)
let ticker: ReturnType<typeof setInterval> | undefined
onMounted(async () => {
  try {
    const response = await fetch('/demo-api/status', { headers: { 'X-Demo-Client': 'slidev' } })
    ready.value = response.ok && (await response.json()).ready
  } catch (cause) { ready.value = false; error.value = cause instanceof Error ? cause.message : 'Local adapter unavailable.' }
})
async function invoke() {
  busy.value = true; error.value = ''; output.value = ''; raw.value = undefined; result.value = undefined; elapsed.value = 0
  const started = performance.now()
  ticker = setInterval(() => { elapsed.value = performance.now() - started }, 100)
  try {
    result.value = await streamDemo('probe', event => {
      if (event.type === 'delta') output.value += event.text
      if (event.type === 'tool' || event.type === 'step') output.value += `\n[${event.name ?? event.type}] ${event.detail ?? ''}\n`
    })
    output.value = result.value.text; raw.value = result.value.raw
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'The probe failed.' }
  finally { clearInterval(ticker); elapsed.value = performance.now() - started; busy.value = false }
}
onUnmounted(() => clearInterval(ticker))
const portal = [
  ['Create', 'New Foundry → your existing project → Create an agent. Use a unique name. Keep Text selected. Enable Use the Microsoft Copilot harness.'],
  ['Configure', 'Select gpt-6-luna. Add instructions and cookbook-review. Inspect all five harness tools. Save and start new chat; wait for the active version.'],
  ['Invoke', 'Ask the shared recipe task. Expand the response trace. Inspect file writes, shell checks and the skill. Download the notebook.'],
]
const cli = [
  ['Initialize', '$env:AZD_ALPHA_ENABLE_AGENTS_MANAGED_HARNESS="true"\nazd ai agent init recipe-live --kind prompt --agent-name <unique-name> --project-id $env:PROJECT_ID --model-deployment gpt-6-luna --no-prompt'],
  ['Select harness', '# Keep generated project/model fields in azure.yaml\nharness:\n  type: microsoft_copilot_preview\nskills:\n  - cookbook-review\n# Declare the skill as a sibling azure.ai.skill service.\n# Add it to uses to order deployment.'],
  ['Deploy + invoke', 'azd deploy --all --no-prompt\nazd ai agent show --output json\nazd ai agent invoke --new-conversation --no-prompt "What can you help me do?"\n# Open the same agent in the Foundry playground.'],
]
</script>

<template>
  <section class="demo" :aria-label="`${kind} demonstration runbook`" @click.stop @keydown.stop>
    <div class="toolbar"><button v-for="(item, index) in kind === 'portal' ? portal : cli" :key="index" :aria-pressed="step === index" @click="step = index">{{ index + 1 }} · {{ item[0] }}</button><span class="mode">PRESENTER RUNBOOK</span></div>
    <div class="stage">
      <div><h2>{{ (kind === 'portal' ? portal : cli)[step][0] }}</h2><p>The presenter uses the real {{ kind === 'portal' ? 'Foundry portal' : 'azd terminal' }}.</p><p class="caption">This panel is a runbook, not a simulated portal or terminal.</p></div>
      <pre class="panel">{{ (kind === 'portal' ? portal : cli)[step][1] }}</pre>
    </div>
    <div class="toolbar">
      <button class="primary" :disabled="!ready || busy" @click="invoke">{{ busy ? 'Invoking...' : 'Invoke prepared agent · live' }}</button>
      <button :aria-pressed="resultView === 'text'" @click="resultView = 'text'">Output</button>
      <button :aria-pressed="resultView === 'json'" @click="resultView = 'json'">Raw JSON</button>
      <button :aria-pressed="resultView === 'cost'" @click="resultView = 'cost'">Cost</button>
      <output class="clock" v-if="busy || elapsed">{{ (elapsed / 1000).toFixed(1) }} s</output>
      <span class="status">Calls the prepared agent, not the creation flow.</span>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <pre v-else-if="raw || output" class="probe-output">{{ resultView === 'json' ? JSON.stringify(raw, null, 2) : resultView === 'cost' ? `${result?.usage.input_tokens ?? '—'} input tokens · ${result?.usage.output_tokens ?? '—'} output tokens\n${result?.cost_usd == null ? 'Cost unavailable: verified rates not configured.' : `$${result.cost_usd.toFixed(5)} estimated token cost`}` : output }}</pre>
    <p v-else class="caption">Offline: use slide 12's synthetic recipe fixture. It is not a service recording.</p>
  </section>
</template>
