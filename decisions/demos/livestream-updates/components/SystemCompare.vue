<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { type Answer, api, decisionsBlocker, type DemoStatus, type System1Result, type System2Result, type SystemCode } from '../demo-api'
import CodeBlock from './CodeBlock.vue'

interface Lane<T> { busy: boolean; started: number; result?: T; error: string }
type View = 'result' | 'code' | 'json'

const tickets = {
  mixed: 'I was charged for the Pro plan, but SSO still does not work, and now our admin is locked out.',
  outage: 'Since the 2.14 update, every export to PDF fails with error 0x80070005. Our whole finance team is blocked and month-end close is tomorrow.',
  refund: 'I was charged twice for my annual plan this morning. I only want one subscription. Please return the extra charge to my card.',
  security: "Someone logged in to my account from another country and changed my email address. I did not do this. I can't get back in.",
}
const selected = ref<keyof typeof tickets>('mixed')
const text = ref(tickets.mixed)
const ready = ref(false)
const status = ref('Checking the connection…')
const now = ref(0)
const fast = reactive<Lane<System1Result>>({ busy: false, started: 0, error: '' })
const slow = reactive<Lane<System2Result>>({ busy: false, started: 0, error: '' })
const busy = computed(() => fast.busy || slow.busy)
const views: { id: View; label: string }[] = [{ id: 'result', label: 'Result' }, { id: 'code', label: 'Code' }, { id: 'json', label: 'JSON' }]
const view = ref<View>('result')
const code = ref<SystemCode>()
const codeError = ref('')
let ticker: ReturnType<typeof setInterval> | undefined
let codeTimer: ReturnType<typeof setTimeout> | undefined

const find = <K extends Answer['type']>(type: K, name: string) =>
  fast.result?.answers.find((a): a is Extract<Answer, { type: K }> => a.type === type && a.name === name)
const refund = computed(() => find('predicate', 'wants_refund'))
const team = computed(() => find('choice', 'team'))
const severity = computed(() => find('score', 'severity'))
const severityLabel = computed(() => severity.value?.probabilities.find(p => p.value === Math.round(severity.value!.score))?.label)
const thoughts = computed(() => (slow.result?.summary ?? []).map((part) => {
  const match = /^\*\*(.+?)\*\*\s*/.exec(part)
  const body = match ? part.slice(match[0].length) : part
  return { title: match?.[1] ?? '', paragraphs: body.split(/\n\s*\n/).map(p => p.trim()).filter(Boolean) }
}))
const fastJson = computed(() => fast.result ? JSON.stringify(fast.result.raw, null, 2) : '')
const slowJson = computed(() => slow.result ? JSON.stringify(slow.result.raw, null, 2) : '')

watch(selected, value => { text.value = tickets[value] })
watch(text, () => { for (const lane of [fast, slow]) { lane.result = undefined; lane.error = '' } })
watch([view, text], () => {
  clearTimeout(codeTimer)
  if (view.value === 'code') codeTimer = setTimeout(loadCode, 150)
})

function clock(lane: Lane<System1Result | System2Result>) {
  if (lane.busy) return `${((now.value - lane.started) / 1000).toFixed(1)} s`
  const ms = lane.result?.elapsed_ms
  return ms == null ? '' : `${(ms / 1000).toFixed(1)} s`
}

function price(lane: Lane<System1Result | System2Result>) {
  const usd = lane.result?.cost_usd
  if (usd == null) return ''
  const perThousand = usd * 1000
  return `≈ $${perThousand >= 1 ? perThousand.toFixed(2) : perThousand.toPrecision(2)} / 1K runs`
}

function priceNote(lane: Lane<System1Result | System2Result>) {
  const usd = lane.result?.cost_usd
  return usd == null ? '' : `$${usd.toPrecision(3)} for this run. Estimate at Azure list price for gpt-6-luna, Global Standard.`
}

async function loadCode() {
  const sent = text.value
  try {
    const result = await api<SystemCode>('system-code', { text: sent })
    if (sent === text.value) { code.value = result; codeError.value = '' }
  }
  catch (cause) { codeError.value = cause instanceof Error ? cause.message : 'Cannot build the request.' }
}

async function runLane<T>(lane: Lane<T>, path: string) {
  lane.busy = true
  lane.error = ''
  lane.result = undefined
  lane.started = performance.now()
  try { lane.result = await api<T>(path, { mode: 'live', text: text.value }) }
  catch (cause) { lane.error = cause instanceof Error ? cause.message : 'The request failed.' }
  finally { lane.busy = false }
}

async function runBoth() {
  if (busy.value || !ready.value) return
  now.value = performance.now()
  ticker = setInterval(() => { now.value = performance.now() }, 100)
  try { await Promise.all([runLane(fast, 'system1'), runLane(slow, 'system2')]) }
  finally { clearInterval(ticker) }
}

async function checkStatus() {
  try {
    const blocker = decisionsBlocker(await api<DemoStatus>('status'))
    ready.value = !blocker
    status.value = blocker ?? ''
  }
  catch (cause) {
    ready.value = false
    status.value = cause instanceof Error ? cause.message : 'Cannot reach the demo server.'
  }
}
onMounted(checkStatus)
onUnmounted(() => { clearInterval(ticker); clearTimeout(codeTimer) })
</script>

<template>
  <section class="demo compare" aria-label="System 1 and System 2 comparison" @keydown.stop @click.stop>
    <div class="demo-toolbar">
      <label>Ticket
        <select v-model="selected" :disabled="busy">
          <option value="mixed">Mixed signals</option>
          <option value="outage">Team blocked</option>
          <option value="refund">Duplicate charge</option>
          <option value="security">Account takeover</option>
        </select>
      </label>
      <div class="view-switch" role="group" aria-label="Lane view">
        <button v-for="item in views" :key="item.id" :aria-pressed="view === item.id" @click="view = item.id">{{ item.label }}</button>
      </div>
      <span v-if="!ready" class="run-status" role="status">{{ status }}</span>
    </div>
    <div class="compare-input">
      <textarea v-model="text" aria-label="Ticket text" :disabled="busy" maxlength="2000" rows="2" />
      <button class="primary" :disabled="busy || !ready || !text.trim()" @click="runBoth">{{ busy ? 'Running…' : 'Run both' }}</button>
    </div>
    <div class="compare-lanes">
      <article class="lane" aria-live="polite" :aria-busy="fast.busy">
        <header>
          <div><span class="lane-kicker">System 1 · fast</span><strong>Decisions API</strong><small>One pass. Typed answers.</small></div>
          <div class="lane-stats"><output class="lane-clock">{{ clock(fast) }}</output><small v-if="price(fast)" class="lane-cost" :title="priceNote(fast)">{{ price(fast) }}</small></div>
        </header>
        <CodeBlock v-if="view === 'code' && code" :source="code.system1" label="System 1 request code" />
        <p v-else-if="view === 'code'" class="lane-empty">{{ codeError || 'Building the request…' }}</p>
        <p v-else-if="fast.error" role="alert" class="error">{{ fast.error }}</p>
        <p v-else-if="!fast.result" class="lane-empty">{{ fast.busy ? 'Answering three typed questions…' : view === 'json' ? 'Run both to see the raw response.' : 'wants_refund · team · severity' }}</p>
        <CodeBlock v-else-if="view === 'json'" :source="fastJson" label="System 1 raw response" />
        <template v-else>
          <div class="probability-row">
            <span>refund</span>
            <div class="probability-track"><div :style="{ width: `${(refund?.probability ?? 0) * 100}%` }" /></div>
            <output>{{ refund ? `${(refund.probability * 100).toFixed(0)}%` : 'refused' }}</output>
          </div>
          <div class="lane-line"><span>team</span><strong>{{ team?.choice ?? 'refused' }}</strong><span v-if="team" class="lane-meta">confidence {{ team.confidence.toFixed(2) }}</span></div>
          <div v-for="option in team?.probabilities ?? []" :key="option.value" class="probability-row">
            <span>{{ option.value }}</span>
            <div class="probability-track"><div :style="{ width: `${option.probability * 100}%` }" /></div>
            <output>{{ (option.probability * 100).toFixed(1) }}%</output>
          </div>
          <div class="lane-line"><span>severity</span><strong>{{ severity ? `${severity.score.toFixed(2)} / 4` : 'refused' }}</strong><span v-if="severityLabel" class="lane-meta">≈ {{ severityLabel }}</span></div>
          <p class="lane-foot">{{ fast.result.usage.output_tokens }} output tokens · {{ fast.result.usage.input_tokens }} input tokens</p>
        </template>
      </article>
      <article class="lane" aria-live="polite" :aria-busy="slow.busy">
        <header>
          <div><span class="lane-kicker">System 2 · slow</span><strong>Responses API</strong><small>Reasoning effort: high.</small></div>
          <div class="lane-stats"><output class="lane-clock">{{ clock(slow) }}</output><small v-if="price(slow)" class="lane-cost" :title="priceNote(slow)">{{ price(slow) }}</small></div>
        </header>
        <CodeBlock v-if="view === 'code' && code" :source="code.system2" label="System 2 request code" />
        <p v-else-if="view === 'code'" class="lane-empty">{{ codeError || 'Building the request…' }}</p>
        <p v-else-if="slow.error" role="alert" class="error">{{ slow.error }}</p>
        <p v-else-if="!slow.result" class="lane-empty">{{ slow.busy ? 'Thinking…' : view === 'json' ? 'Run both to see the raw response.' : 'Same three questions, as a prompt.' }}</p>
        <CodeBlock v-else-if="view === 'json'" :source="slowJson" label="System 2 raw response" />
        <template v-else>
          <div class="thinking" tabindex="0" aria-label="Reasoning summary">
            <span class="lane-kicker">Thinking · summary</span>
            <p v-if="!thoughts.length">No summary returned.</p>
            <section v-for="(thought, index) in thoughts" :key="index" class="thought">
              <strong v-if="thought.title">{{ thought.title }}</strong>
              <p v-for="(paragraph, line) in thought.paragraphs" :key="line">{{ paragraph }}</p>
            </section>
          </div>
          <p class="lane-answer" tabindex="0">{{ slow.result.text }}</p>
          <p class="lane-foot">{{ slow.result.usage.output_tokens }} output tokens · {{ slow.result.usage.reasoning_tokens }} reasoning</p>
        </template>
      </article>
    </div>
  </section>
</template>
