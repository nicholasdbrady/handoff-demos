<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, decisionsBlocker, type DemoStatus, type NativeResult } from '../demo-api'
import CodeBlock from './CodeBlock.vue'
import RunMetrics from './RunMetrics.vue'

type Match = 'same' | 'different' | 'review'
interface Product { name: string; image: string; [key: string]: string }
interface Pair { id: string; title: string; left: Product; right: Product; expected: Match; reason: string }
interface Item { result?: NativeResult; error?: string; pending?: boolean }
interface Lane {
  id: 'luna' | 'microsoft'
  title: string
  busy: boolean
  items: Record<string, Item>
  summary?: NativeResult
}
const lanes = reactive<Lane[]>([
  { id: 'luna', title: 'Luna', busy: false, items: {} },
  { id: 'microsoft', title: 'Decision-1', busy: false, items: {} },
])
const pairs = ref<Pair[]>([])
const selected = ref(0)
const pair = computed(() => pairs.value[selected.value])
const busy = computed(() => lanes.some(lane => lane.busy))
const status = ref('Checking both deployments…')
const ready = ref(false)
const view = ref<'pairs' | 'request' | 'json'>('pairs')
const requests = ref<{ luna: unknown; microsoft: unknown }>()
const previewError = ref('')
let revision = 0
const labels: Record<Match, string> = { same: 'Same', different: 'Different', review: 'Review' }

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function verdict(item?: Item): Match | 'refused' | 'invalid' | undefined {
  if (!item?.result) return undefined
  const raw = item.result.raw
  if (!record(raw)) return 'invalid'
  const answers = raw.answers
  let answer: unknown
  if (Array.isArray(answers)) {
    if (answers.length !== 1 || !record(answers[0]) || answers[0].name !== 'match') return 'invalid'
    answer = answers[0]
  }
  else if (record(answers) && Object.keys(answers).length === 1) answer = answers.match
  if (!record(answer)) return 'invalid'
  if (answer.type === 'refusal') return 'refused'
  return answer.type === 'choice' && (answer.choice === 'same' || answer.choice === 'different' || answer.choice === 'review')
    ? answer.choice : 'invalid'
}
function cell(lane: Lane, entry: Pair) {
  const item = lane.items[entry.id]
  if (item?.error) return 'Error'
  if (item?.pending) return 'Working…'
  const value = verdict(item)
  return value === 'invalid' ? 'Invalid' : value === 'refused' ? 'Refused' : value ? labels[value] : '—'
}
function outcome(lane: Lane, entry: Pair) {
  const item = lane.items[entry.id]
  if (item?.error || (item?.result && verdict(item) !== entry.expected)) return 'mismatch'
  return item?.result ? 'matched' : ''
}
function completed(lane: Lane) {
  return Object.values(lane.items).filter(item => item.result || item.error).length
}
function returned(lane: Lane) {
  return Object.values(lane.items).filter(item => item.result).length
}
function matches(lane: Lane) {
  return pairs.value.filter(entry => verdict(lane.items[entry.id]) === entry.expected).length
}
function attributes(product: Product) {
  return Object.entries(product).filter(([key]) => !['name', 'image'].includes(key))
}
async function loadRequests() {
  if (!pair.value) return
  const current = ++revision
  requests.value = undefined
  previewError.value = ''
  try {
    const result = await api<{ luna: unknown; microsoft: unknown }>('catalog-code', { pair: pair.value.id })
    if (current === revision) requests.value = result
  }
  catch (cause) {
    if (current === revision) previewError.value = cause instanceof Error ? cause.message : 'Cannot load requests. Retry by selecting a pair.'
  }
}
async function runLane(lane: Lane) {
  lane.busy = true
  try {
    for (const entry of pairs.value) {
      lane.items[entry.id] = { pending: true }
      try {
        const result = await api<NativeResult>('catalog-decision', { mode: 'live', provider: lane.id, pair: entry.id })
        lane.items[entry.id] = { result }
      }
      catch (cause) {
        lane.items[entry.id] = { error: cause instanceof Error ? cause.message : 'Provider request failed.' }
      }
    }
    const results = Object.values(lane.items).flatMap(item => item.result ? [item.result] : [])
    const allLive = results.length === pairs.value.length && results.every(result => result.mode === 'live')
    const knownCost = allLive && results.every(result => typeof result.cost_usd === 'number' && Number.isFinite(result.cost_usd) && result.cost_usd >= 0)
    lane.summary = {
      mode: results.length === pairs.value.length && results.every(result => result.mode === 'rehearsal') ? 'rehearsal' : 'live',
      elapsed_ms: allLive && results.every(result => result.elapsed_ms != null)
        ? results.reduce((sum, result) => sum + result.elapsed_ms!, 0) : null,
      cost_usd: knownCost ? results.reduce((sum, result) => sum + result.cost_usd!, 0) : null,
      cost_note: 'Sum of returned usage estimates divided by 12 pairs, extrapolated to 1,000 pairs. Any error or missing cost makes the estimate unavailable. Not an invoice.',
      raw: null,
    }
  }
  finally { lane.busy = false }
}
async function runBatch() {
  if (busy.value || !ready.value) return
  for (const lane of lanes) { lane.items = {}; lane.summary = undefined }
  view.value = 'pairs'
  await Promise.all(lanes.map(runLane))
}
watch(() => pair.value?.id, loadRequests)
onMounted(async () => {
  try {
    const [fixtures, config] = await Promise.all([
      api<{ pairs: Pair[] }>('catalog-fixtures'), api<DemoStatus>('status'),
    ])
    pairs.value = fixtures.pairs
    status.value = decisionsBlocker(config) ?? (!config.systemone_configured
      ? 'Set SYSTEMONE_ENDPOINT and SYSTEMONE_DEPLOYMENT, then restart the adapter.' : '')
    ready.value = !status.value && pairs.value.length > 0
  }
  catch (cause) { status.value = cause instanceof Error ? cause.message : 'Cannot reach the adapter. Restart demo_server.py.' }
})
</script>

<template>
  <section class="demo provider-compare catalog-demo" aria-label="Product matching batch comparison" @keydown.stop @click.stop>
    <div class="demo-toolbar catalog-toolbar">
      <div class="view-switch" role="group" aria-label="Provider comparison view">
        <button :aria-pressed="view === 'pairs'" @click="view = 'pairs'">Product pairs</button>
        <button :aria-pressed="view === 'request'" @click="view = 'request'">Request</button>
        <button :aria-pressed="view === 'json'" @click="view = 'json'">JSON</button>
      </div>
      <span class="micro">12 pairs · one call at a time per provider</span>
      <button class="primary" :disabled="busy || !ready" @click="runBatch">{{ busy ? 'Processing batch…' : 'Run 12 pairs' }}</button>
    </div>
    <p v-if="status" role="status" class="micro">{{ status }}</p>
    <div v-if="pair" class="catalog-workspace">
      <div class="catalog-evidence">
        <h2>{{ pair.title }}</h2>
        <div class="product-pair">
          <article v-for="(product, index) in [pair.left, pair.right]" :key="index" class="catalog-product">
            <img :src="`/catalog/${product.image}`" alt="Decorative product photo; compare the listed attributes, not the image." />
            <small>{{ index === 0 ? 'Catalog A' : 'Catalog B' }}</small>
            <h3>{{ product.name }}</h3>
            <dl><div v-for="[key, value] in attributes(product)" :key="key" :class="{ 'attribute-diff': pair.left[key] !== pair.right[key] }"><dt>{{ key }}</dt><dd>{{ value }}</dd></div></dl>
          </article>
        </div>
        <div class="catalog-reference">
          <strong>Reference: {{ labels[pair.expected] }}</strong>
          <p>{{ pair.reason }}</p>
        </div>
      </div>
      <div class="catalog-results">
        <div class="catalog-summaries">
          <article v-for="lane in lanes" :key="lane.id" class="catalog-lane" :aria-label="lane.title" :aria-busy="lane.busy">
            <div><strong>{{ lane.title }}</strong><span>{{ completed(lane) }} / {{ pairs.length }} processed</span><span>{{ matches(lane) }} / {{ completed(lane) }} reference matches</span></div>
            <RunMetrics :busy="lane.busy" :result="lane.summary" :pairs="pairs.length" :processed="returned(lane)" />
          </article>
        </div>
        <div v-if="view === 'pairs'" class="catalog-table-wrap">
          <table class="catalog-table">
            <thead><tr><th>Product pair</th><th>Luna</th><th>Decision-1</th></tr></thead>
            <tbody><tr v-for="(entry, index) in pairs" :key="entry.id" :class="{ selected: selected === index }">
              <th><button :aria-pressed="selected === index" @click="selected = index">{{ index + 1 }}. {{ entry.title }}</button></th>
              <td v-for="lane in lanes" :key="lane.id" :class="outcome(lane, entry)" :title="lane.items[entry.id]?.error || (outcome(lane, entry) === 'matched' ? 'Matches authored reference' : outcome(lane, entry) === 'mismatch' ? 'Does not match reference; inspect JSON' : '')">{{ cell(lane, entry) }}<small v-if="outcome(lane, entry)">{{ outcome(lane, entry) === 'matched' ? 'match' : 'check' }}</small></td>
            </tr></tbody>
          </table>
        </div>
        <div v-else class="catalog-inspect">
          <label>Inspect pair <select v-model="selected" aria-label="Inspect product pair"><option v-for="(entry, index) in pairs" :key="entry.id" :value="index">{{ index + 1 }}. {{ entry.title }}</option></select></label>
          <p v-if="previewError && view === 'request'" role="alert" class="error">{{ previewError }}</p>
          <div v-for="lane in lanes" :key="lane.id">
            <strong>{{ lane.title }}</strong>
            <CodeBlock v-if="view === 'request' && requests" :label="`${lane.id} request`" :source="JSON.stringify(requests[lane.id], null, 2)" />
            <CodeBlock v-else-if="view === 'json' && lane.items[pair.id]?.result" :label="`${lane.id} native JSON`" :source="JSON.stringify(lane.items[pair.id]?.result?.raw, null, 2)" />
            <p v-else-if="view === 'json' && lane.items[pair.id]?.error" role="alert" class="error">{{ lane.items[pair.id]?.error }}</p>
            <p v-else class="micro">{{ view === 'request' ? 'Loading request…' : 'No response for this pair yet.' }}</p>
          </div>
        </div>
        <p v-if="lanes.some(lane => Object.values(lane.items).some(item => item.error))" role="alert" class="error catalog-error">Some requests failed. Select JSON and the affected pair for the error. Costs are unavailable for incomplete usage.</p>
        <p v-if="lanes.some(lane => Object.values(lane.items).some(item => item.result?.mode === 'rehearsal'))" class="micro">REHEARSAL · synthetic reference answers, not model quality or throughput</p>
      </div>
    </div>
    <p class="micro catalog-disclaimer">Synthetic text-only set, not a benchmark. Photos are decorative. Quality = reference-label agreement. Select a row to inspect; no records are merged.</p>
  </section>
</template>
