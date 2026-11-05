<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, decisionsBlocker, type DecisionResult, type DemoStatus } from '../demo-api'

const ready = ref(false)
const status = ref('Checking the connection…')
const busy = ref(false)
const error = ref('')
const result = ref<DecisionResult>()
const threshold = ref(0.85)
const examples = {
  refund: 'I was charged twice for my annual plan this morning. I only want one subscription. Please return the extra charge to my card.',
  security: "Someone logged in to my account from another country and changed my email address. I did not do this. I can't get back in.",
  outage: 'Since the 2.14 update, every export to PDF fails with error 0x80070005. Our whole finance team is blocked and month-end close is tomorrow.',
  unclear: 'The new dark theme looks great, thanks team!',
}
const selected = ref<keyof typeof examples>('refund')
const text = ref(examples.refund)
const department = computed(() => result.value?.answers.filter(a => a.type === 'choice').find(a => a.name === 'department'))
const severity = computed(() => result.value?.answers.filter(a => a.type === 'score').find(a => a.name === 'severity'))
const predicates = computed(() => result.value?.answers.filter(a => a.type === 'predicate') ?? [])
const suggestion = computed(() => {
  if (!result.value) return 'Run the triage pack to see a suggested route.'
  if (result.value.answers.some(a => a.type === 'refusal')) return 'Human review: at least one question was refused.'
  if (!department.value || !severity.value || predicates.value.length !== 4) return 'Human review: the answer set is incomplete.'
  const risk = predicates.value.find(a => a.name === 'security_risk')
  if (risk && risk.probability >= threshold.value) return 'Suggested route: security review.'
  if (department.value.confidence < threshold.value || department.value.choice === 'other') return 'Human review: no sufficiently confident department.'
  return `Suggested queue: ${department.value.choice}.`
})

watch(selected, value => { text.value = examples[value] })
watch(text, () => { result.value = undefined; error.value = '' })

async function checkStatus() {
  try {
    const blocker = decisionsBlocker(await api<DemoStatus>('status'))
    ready.value = !blocker
    status.value = blocker ?? ''
    error.value = ''
  }
  catch (cause) {
    ready.value = false
    status.value = cause instanceof Error ? cause.message : 'Cannot reach the demo server.'
  }
}

async function run() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  result.value = undefined
  try { result.value = await api<DecisionResult>('decisions', { mode: 'live', text: text.value }) }
  catch (cause) { error.value = cause instanceof Error ? cause.message : 'The decision request failed.' }
  finally { busy.value = false }
}
onMounted(checkStatus)
</script>

<template>
  <section class="demo" aria-label="Interactive Decisions API demo" @keydown.stop @click.stop>
    <div v-if="!ready" class="demo-toolbar">
      <span class="run-status" role="status">{{ status }}</span>
    </div>
    <div class="decision-workspace">
      <div class="evidence">
        <label for="ticket-example">Customer ticket</label>
        <select id="ticket-example" v-model="selected" :disabled="busy">
          <option value="refund">Duplicate charge</option>
          <option value="security">Account takeover</option>
          <option value="outage">Team blocked</option>
          <option value="unclear">General feedback</option>
        </select>
        <textarea v-model="text" aria-label="Ticket evidence" :disabled="busy" maxlength="6000" rows="4" />
        <button class="primary" :disabled="busy || !ready || !text.trim()" @click="run">
          {{ busy ? 'Evaluating ticket…' : 'Run 6 questions' }}
        </button>
        <p class="micro">One input. Predicate, choice, and score in one request.</p>
      </div>
      <div class="answers" aria-live="polite" :aria-busy="busy">
        <div v-if="!result" class="empty-state">
          <strong>{{ busy ? 'Waiting for typed answers' : 'Evidence in. Typed answers out.' }}</strong>
          <p>{{ busy ? 'The service is evaluating the same input against six independent questions.' : 'Choose a ticket, then run the triage pack. The result will show distributions, not generated explanations.' }}</p>
        </div>
        <template v-else>
          <div class="result-heading"><strong>{{ department?.choice ?? 'Review required' }}</strong><span v-if="result.elapsed_ms !== null">{{ result.elapsed_ms }} ms</span></div>
          <div v-for="option in department?.probabilities ?? []" :key="option.value" class="probability-row">
            <span>{{ option.value }}</span>
            <div class="probability-track"><div :style="{ width: `${option.probability * 100}%` }" /></div>
            <output>{{ (option.probability * 100).toFixed(1) }}%</output>
          </div>
          <div class="answer-summary">
            <span>Severity <strong>{{ severity?.score.toFixed(2) ?? 'refused' }} / 4</strong></span>
            <span>Choice confidence <strong>{{ department?.confidence.toFixed(2) ?? 'refused' }}</strong></span>
          </div>
          <div class="predicate-list">
            <span v-for="answer in predicates" :key="answer.name">{{ answer.name.replaceAll('_', ' ') }} <strong>{{ answer.probability.toFixed(2) }}</strong></span>
          </div>
          <p class="micro">{{ result.usage.input_tokens }} input tokens · {{ result.usage.output_tokens }} output tokens</p>
        </template>
      </div>
    </div>
    <div class="policy-strip">
      <label for="threshold">Demo threshold <output>{{ threshold.toFixed(2) }}</output></label>
      <input id="threshold" v-model.number="threshold" type="range" min="0.5" max="0.99" step="0.01">
      <span>{{ suggestion }}</span>
    </div>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
  </section>
</template>
