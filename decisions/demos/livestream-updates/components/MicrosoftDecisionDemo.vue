<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type DemoStatus, type NativeResult } from '../demo-api'
import RunMetrics from './RunMetrics.vue'
import CodeBlock from './CodeBlock.vue'

const text = ref('We were billed twice. Please refund the duplicate charge.')
const code = ref('')
const typescript = ref('')
const result = ref<NativeResult>()
const view = ref<'code' | 'typescript' | 'response' | 'json'>('code')
const ready = ref(false)
const status = ref('Checking configuration…')
const error = ref('')
const busy = ref(false)
let revision = 0
const severityLevels = ['Cosmetic', 'Minor', 'Major', 'Critical']

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

const response = computed(() => {
  if (!result.value) return null
  const raw = result.value.raw
  if (!isRecord(raw) || !isRecord(raw.answers)) return null
  const { refund_requested: refund, team, severity } = raw.answers
  if (!isRecord(refund) || refund.type !== 'noul' || typeof refund.noul !== 'number'
    || !Number.isFinite(refund.noul) || refund.noul < 0 || refund.noul > 1
    || !isRecord(team) || team.type !== 'choice' || typeof team.choice !== 'string'
    || !['billing', 'technical', 'other'].includes(team.choice)
    || !isRecord(severity) || severity.type !== 'score' || typeof severity.score !== 'number'
    || !Number.isFinite(severity.score) || severity.score < 0 || severity.score > 3) return null
  return { refund: refund.noul, team: team.choice, severity: severity.score }
})

async function loadCode() {
  const current = ++revision
  result.value = undefined
  code.value = ''
  typescript.value = ''
  error.value = ''
  try {
    const response = await api<{ code: string; typescript: string }>('microsoft-code', { text: text.value })
    if (current === revision) {
      code.value = response.code
      typescript.value = response.typescript
    }
  }
  catch (cause) {
    if (current === revision) error.value = cause instanceof Error ? cause.message : 'Cannot load the SDK examples.'
  }
}

async function run() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  result.value = undefined
  view.value = 'response'
  try { result.value = await api<NativeResult>('microsoft-decision', { mode: 'live', text: text.value }) }
  catch (cause) { error.value = cause instanceof Error ? cause.message : 'System One request failed.' }
  finally { busy.value = false }
}

watch(text, loadCode)
onMounted(async () => {
  await loadCode()
  try {
    const config = await api<DemoStatus>('status')
    status.value = !config.live_enabled
      ? 'Set SLIDEV_ENABLE_LIVE=1 and restart the adapter.'
      : !config.systemone_configured
          ? 'Optional: set SYSTEMONE_ENDPOINT and SYSTEMONE_DEPLOYMENT for Microsoft-Decision-1, then restart.'
          : ''
    ready.value = !status.value
  }
  catch (cause) { status.value = cause instanceof Error ? cause.message : 'Cannot reach the adapter.' }
})
</script>

<template>
  <section class="demo microsoft-demo" aria-label="Microsoft-Decision-1 SDK examples and native demo" @keydown.stop @click.stop>
    <div v-if="!ready" class="demo-toolbar"><span class="run-status" role="status">{{ status }}</span></div>
    <div class="compare-input">
      <textarea v-model="text" aria-label="Microsoft decision ticket" rows="2" maxlength="6000" :disabled="busy" />
      <button class="primary" :disabled="busy || !ready || !text.trim()" @click="run">{{ busy ? 'Evaluating…' : 'Run Decision-1' }}</button>
    </div>
    <div class="native-toolbar">
      <div class="view-switch" role="group" aria-label="Microsoft decision view">
        <button :aria-pressed="view === 'code'" @click="view = 'code'">Python</button>
        <button :aria-pressed="view === 'typescript'" @click="view = 'typescript'">TypeScript</button>
        <button :aria-pressed="view === 'response'" @click="view = 'response'">Response</button>
        <button :aria-pressed="view === 'json'" @click="view = 'json'">JSON</button>
      </div>
      <span class="micro native-endpoint">{{ result?.mode === 'rehearsal' ? 'REHEARSAL · synthetic rendering fixture' : '/providers/microsoft/v1/systemone' }}</span>
      <RunMetrics :busy="busy" :result="result" />
    </div>
    <div class="native-content" :aria-busy="busy">
      <CodeBlock v-if="view === 'code'" class="native-code" label="Microsoft request code" :source="code" />
      <CodeBlock v-else-if="view === 'typescript'" class="native-code" label="Microsoft TypeScript code" :source="typescript" />
      <CodeBlock v-else-if="view === 'json' && result" class="native-code" label="Microsoft response JSON" :source="JSON.stringify(result.raw, null, 2)" />
      <div v-else-if="view === 'response' && response" class="native-response" aria-label="Microsoft visual response">
        <div class="native-answer">
          <div><h2>Refund requested?</h2><p class="micro"><code>refund_requested</code> · noul</p></div>
          <div class="native-answer-value"><strong>{{ (response.refund * 100).toFixed(1) }}%</strong><span>Probability of an explicit money-back request</span>
            <div class="native-meter" role="meter" aria-label="Refund request probability" :aria-valuenow="response.refund" :aria-valuemin="0" :aria-valuemax="1"><div :style="{ width: `${response.refund * 100}%` }" /></div>
          </div>
        </div>
        <div class="native-answer">
          <div><h2>Which team?</h2><p class="micro"><code>team</code> · choice</p></div>
          <div class="native-answer-value"><strong class="native-team">{{ response.team }}</strong><span>Selected from billing, technical, or other</span></div>
        </div>
        <div class="native-answer">
          <div><h2>Business impact</h2><p class="micro"><code>severity</code> · score</p></div>
          <div class="native-answer-value"><strong>{{ response.severity.toFixed(2) }} <small>/ 3</small></strong><span>Probability-weighted score, not a rounded category</span>
            <div class="native-meter" role="meter" aria-label="Business impact score" :aria-valuenow="response.severity" :aria-valuemin="0" :aria-valuemax="3"><div :style="{ width: `${response.severity / 3 * 100}%` }" /></div>
            <div class="native-scale"><span v-for="(level, index) in severityLevels" :key="level">{{ index }} {{ level }}</span></div>
          </div>
        </div>
        <p class="micro">Three independent judgments. Your application sets review thresholds and decides what happens next.</p>
      </div>
      <p v-else-if="view === 'response' && result" role="alert" class="error">Cannot display these answers visually. Open JSON to inspect the native response; expected refund_requested (noul), team (choice), and severity (score).</p>
      <p v-else class="native-empty" role="status">{{ busy ? 'Evaluating the ticket…' : "Run to inspect the service's three named answers. No generated explanation is requested." }}</p>
    </div>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p class="micro">TypeSafe SDKs + Entra. Replace the resource URL and deployment name. Run sends the same native payload through the local adapter.</p>
  </section>
</template>
