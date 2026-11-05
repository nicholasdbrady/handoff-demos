<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api, decisionsBlocker, type DemoStatus, type NativeResult } from '../demo-api'
import CodeBlock from './CodeBlock.vue'
import RunMetrics from './RunMetrics.vue'

type Fixture = 'clear' | 'low_ocr' | 'missing_region' | 'contradiction' | 'reason_code'
interface Checks {
  status: 'review' | 'matched' | 'partial_delivery' | 'semantic_needed'
  reason: string
  short_cases: number | null
  reference_usd: string | null
}
interface Evidence {
  document_id: string; ordered: string; listed: string; received: string; unit_price: string
  currency: string; note: string; reason_code: string | null
  recognition_confidence: number
  field_confidence: Record<string, number>
  source_regions: Record<string, unknown>
}
interface Preview { evidence: Evidence; checks: Checks; code: string }
interface Result extends NativeResult { checks: Checks; route: { label: string; reason: string } }
const fixture = ref<Fixture>('clear')
const preview = ref<Preview>()
const result = ref<Result>()
const busy = ref(false)
const loading = ref(false)
const ready = ref(false)
const status = ref('')
const error = ref('')
const view = ref<'pipeline' | 'code' | 'json'>('pipeline')
let revision = 0
const routeLabel: Record<string, string> = { partial_delivery: 'Partial-delivery staff queue', damage: 'Damage-review staff queue', review: 'Staff review' }

async function checkEvidence() {
  const current = ++revision
  result.value = undefined
  preview.value = undefined
  error.value = ''
  loading.value = true
  try {
    const data = await api<Preview>('retail-check', { fixture: fixture.value })
    if (current === revision) preview.value = data
  }
  catch (cause) { if (current === revision) error.value = cause instanceof Error ? cause.message : 'Cannot check receiving evidence.' }
  finally { if (current === revision) loading.value = false }
}
async function routeNote() {
  if (busy.value || !ready.value || preview.value?.checks.status !== 'semantic_needed') return
  busy.value = true
  error.value = ''
  result.value = undefined
  view.value = 'pipeline'
  try { result.value = await api<Result>('retail-decision', { fixture: fixture.value, mode: 'live' }) }
  catch (cause) { error.value = cause instanceof Error ? cause.message : 'Delivery-note routing failed.' }
  finally { busy.value = false }
}
watch(fixture, checkEvidence)
onMounted(async () => {
  await checkEvidence()
  try {
    status.value = decisionsBlocker(await api<DemoStatus>('status')) ?? ''
    ready.value = !status.value
  }
  catch (cause) { status.value = cause instanceof Error ? cause.message : 'Cannot reach the adapter.' }
})
</script>

<template>
  <section class="demo retail-demo" aria-label="Retail receiving evidence" @keydown.stop @click.stop>
    <div class="demo-toolbar">
      <label>Evidence
        <select v-model="fixture" aria-label="Receiving scenario" :disabled="busy || loading">
          <option value="clear">Clear source · ambiguous note</option>
          <option value="low_ocr">Low OCR confidence</option>
          <option value="missing_region">Missing note region</option>
          <option value="contradiction">Contradictory quantities</option>
          <option value="reason_code">Structured reason · skip model</option>
        </select>
      </label>
      <span class="micro">Synthetic extraction fixture · no live OCR / DI / CU call</span>
    </div>
    <div v-if="preview" class="retail-workspace">
      <div class="retail-evidence">
        <div class="packing-slip">
          <h2>Supplier packing slip</h2>
          <p class="micro">{{ preview.evidence.document_id }} · illustrative normalized regions in JSON</p>
          <dl>
            <div><dt>Listed quantity</dt><dd>{{ preview.evidence.listed }} cases</dd></div>
            <div><dt>Unit price</dt><dd>USD {{ preview.evidence.unit_price }} / case</dd></div>
          </dl>
          <blockquote :class="{ 'region-missing': !preview.evidence.source_regions.note }">{{ preview.evidence.note }}</blockquote>
          <p class="micro">Note region: {{ preview.evidence.source_regions.note ? 'page 1 · retained' : 'MISSING · review' }}</p>
        </div>
        <div class="receiving-record">
          <h2>Order + receiving record</h2>
          <p>{{ preview.evidence.ordered }} cases ordered · {{ preview.evidence.received }} received</p>
          <p v-if="preview.evidence.reason_code" class="micro">Reason code: {{ preview.evidence.reason_code }}</p>
        </div>
        <p class="micro">OCR {{ preview.evidence.recognition_confidence.toFixed(2) }} · note extraction {{ preview.evidence.field_confidence.note.toFixed(2) }}<br>Recognition, extraction, and decision confidence are different signals.</p>
      </div>
      <div class="retail-output" :aria-busy="busy || loading">
        <div class="image-output-toolbar">
          <div class="view-switch" role="group" aria-label="Retail result view">
            <button :aria-pressed="view === 'pipeline'" @click="view = 'pipeline'">Evidence → route</button>
            <button :aria-pressed="view === 'code'" @click="view = 'code'">Python</button>
            <button :aria-pressed="view === 'json'" @click="view = 'json'">JSON</button>
          </div>
          <RunMetrics :busy="busy" :result="result" />
        </div>
        <CodeBlock v-if="view === 'code'" label="Retail semantic request code" :source="preview.code" />
        <CodeBlock v-else-if="view === 'json'" label="Retail evidence and decision JSON" :source="JSON.stringify({ ...preview, code: undefined, decision: result }, null, 2)" />
        <div v-else class="receiving-pipeline" aria-live="polite">
          <h2>{{ preview.checks.status === 'review' ? 'Review the source first.' : 'Exact checks stay in code.' }}</h2>
          <p v-if="preview.checks.short_cases !== null" class="receiving-math">{{ preview.evidence.listed }} − {{ preview.evidence.received }} = <strong>{{ preview.checks.short_cases }} cases short</strong><br>{{ preview.checks.short_cases }} × USD {{ preview.evidence.unit_price }} = <strong>USD {{ preview.checks.reference_usd }}</strong></p>
          <p v-if="preview.checks.reference_usd" class="micro">Reference value only, not a payable claim or refund.</p>
          <p class="receiving-gate" :data-status="preview.checks.status">{{ preview.checks.reason }}</p>
          <template v-if="result">
            <strong class="receiving-route">{{ routeLabel[result.route.label] ?? 'Staff review' }}</strong>
            <p>{{ result.route.reason }}</p>
            <p v-if="result.mode === 'rehearsal'" class="micro">REHEARSAL · synthetic judgment, not model accuracy evidence</p>
          </template>
          <p v-else-if="preview.checks.status === 'semantic_needed'">Only the note needs a semantic judgment: held for later delivery, damage, or unclear?</p>
          <p v-else-if="preview.checks.status === 'partial_delivery'" class="receiving-route">Partial-delivery staff queue · no model call</p>
          <p class="micro">DI / CU source regions usually remove the need for another box-finding stage. Confidence gates here are illustrative, not calibrated.</p>
        </div>
        <p v-if="status" role="status" class="micro">{{ status }}</p>
        <p v-if="error" role="alert" class="error">{{ error }}</p>
        <button class="primary" :disabled="busy || !ready || preview.checks.status !== 'semantic_needed'" @click="routeNote">{{ busy ? 'Routing the note…' : 'Route note with Luna' }}</button>
      </div>
    </div>
    <p v-else-if="error" role="alert" class="error">{{ error }}</p>
    <p v-else role="status">Checking synthetic extraction evidence…</p>
  </section>
</template>
