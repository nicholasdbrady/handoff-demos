<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { LiveResult } from '../demo-stream'
import { presentationJson, provenanceLabel, toolIcon, toolTitle, type ChatEntry } from '../chat-transcript'

const props = withDefaults(defineProps<{
  title: string; subtitle?: string; avatar?: string; model?: string; task: string
  entries: ChatEntry[]; result?: LiveResult | null; error?: string
  running?: boolean; queued?: boolean; recorded?: boolean; disabled?: boolean
  elapsed?: number; code?: string; raw?: unknown; stoppable?: boolean; stopHint?: string; emptyText?: string
}>(), { model: 'gpt-6-luna', avatar: 'A', elapsed: 0 })
const emit = defineEmits<{ send: []; stop: [] }>()
const view = ref('chat')
const expanded = ref(false)
const transcript = ref<HTMLElement>()
const pinned = ref(true)
const status = computed(() => props.running && props.entries.at(-1)?.name === 'quota_wait' ? 'Rate limited'
  : props.running ? 'Running' : props.queued ? 'Queued'
  : props.error ? 'Error' : props.result ? 'Done' : 'Idle')
const calls = computed(() => props.entries.filter(entry => entry.call).length)
const firstText = computed(() => props.result?.first_text_ms ?? props.entries.find(entry => entry.kind === 'assistant')?.at_ms)
const reasoningTokens = computed(() => props.result?.usage.output_tokens_details?.reasoning_tokens)
const summaryText = computed(() => props.entries.filter(entry => entry.kind === 'reasoning').map(entry => entry.text).filter(Boolean).join('\n\n'))
const stages = computed(() => props.entries.flatMap(entry =>
  entry.kind === 'step' || entry.kind === 'tool' || entry.kind === 'reasoning'
    ? [{ id: entry.id, at: entry.at_ms, label: entry.kind === 'reasoning' ? 'Reasoning summary' : toolTitle(entry.name ?? entry.kind), state: entry.state }]
    : []))
const thinkingLabel = computed(() => props.recorded ? (props.result?.mode === 'synthetic' ? 'Synthetic illustration' : 'Recorded reasoning & activity')
  : props.queued ? `Waiting for the other lane · ${(props.elapsed / 1000).toFixed(1)} s`
  : props.running && firstText.value === undefined
    ? `${props.entries.some(entry => entry.kind === 'reasoning') ? 'Thinking' : 'Waiting for response'} · ${(props.elapsed / 1000).toFixed(1)} s`
    : firstText.value != null ? `First text in ${(firstText.value / 1000).toFixed(1)} s` : 'Reasoning & activity')
const tokenText = computed(() => {
  const usage = props.result?.usage
  return usage?.input_tokens !== undefined && usage?.output_tokens !== undefined
    ? `${usage.input_tokens.toLocaleString()} in / ${usage.output_tokens.toLocaleString()} out`
    : 'Tokens unknown'
})
function onScroll() {
  const node = transcript.value
  if (node) pinned.value = node.scrollHeight - node.clientHeight - node.scrollTop < 50
}
watch(() => [props.entries.map(entry => `${entry.text}|${entry.state}`).join(''), props.result, props.error, view.value], async () => {
  await nextTick()
  if (pinned.value && transcript.value) transcript.value.scrollTop = transcript.value.scrollHeight
})
watch(() => props.running, running => { if (running) { pinned.value = true; view.value = 'chat' } })
function fileHref(file: NonNullable<LiveResult['files']>[number]): string {
  if (file.content !== undefined) return `data:application/json;charset=utf-8,${encodeURIComponent(file.content)}`
  if (props.recorded) return `/recordings/files/${encodeURIComponent(file.name ?? '')}`
  return `/demo-api/files/copilot/${encodeURIComponent(file.id ?? '')}`
}
</script>

<template>
  <article class="chat-window" :aria-label="`${title} chat`" :aria-busy="running">
    <header class="chat-chrome">
      <div class="chat-identity"><span class="chat-avatar" aria-hidden="true">{{ avatar }}</span><div><h2>{{ title }}</h2><p>{{ subtitle }}</p></div></div>
      <div class="chat-presence"><span class="chat-model">{{ model }}</span><span v-if="recorded" class="chat-recorded">{{ result?.mode === 'synthetic' ? 'SYNTHETIC' : 'OFFLINE REPLAY' }}</span><span class="chat-state" :data-state="status.toLowerCase()">{{ status }}</span></div>
    </header>
    <nav class="chat-views" :aria-label="`${title} views`">
      <button v-for="tab in ['chat', 'code', 'json', 'cost']" :key="tab" :aria-pressed="view === tab" @click="view = tab">{{ tab === 'json' ? 'JSON' : tab[0].toUpperCase() + tab.slice(1) }}</button>
      <span>{{ result ? provenanceLabel(result) : subtitle }}</span>
    </nav>
    <div v-if="view === 'chat'" ref="transcript" class="chat-transcript" role="log" :aria-label="`${title} transcript`" aria-live="polite" aria-relevant="additions text" @scroll="onScroll">
      <div class="chat-user-message"><span class="chat-speaker">You</span><p :class="{ 'chat-task-clamped': !expanded }">{{ task }}</p><button :aria-expanded="expanded" @click="expanded = !expanded">{{ expanded ? 'Show less' : 'Show full task' }}</button></div>
      <details v-if="running || queued || entries.length || result || error" class="chat-thinking">
        <summary><span :class="{ 'chat-working': running || queued }">{{ thinkingLabel }}</span><span v-if="reasoningTokens !== undefined">{{ reasoningTokens.toLocaleString() }} reasoning tokens</span></summary>
        <div class="chat-thinking-body">
          <ChatMessage v-if="summaryText" :text="summaryText" />
          <p v-else>{{ running ? 'No summary received yet.' : 'No summary returned.' }} Only supported summaries and observed activity are shown.</p>
          <ol class="chat-stage-list">
            <li v-if="queued"><span>Waiting for the other lane (quota serialization).</span></li>
            <li v-else-if="!recorded"><time>0.0 s</time><span>Request sent</span></li>
            <li v-for="stage in stages" :key="stage.id"><time>{{ stage.at == null ? 'Time unknown' : `${(stage.at / 1000).toFixed(1)} s` }}</time><span>{{ stage.label }}<template v-if="stage.state"> · {{ stage.state }}</template></span></li>
            <li v-if="firstText != null"><time>{{ (firstText / 1000).toFixed(1) }} s</time><span>{{ subtitle?.includes('Nonstreaming') ? 'Nonstreaming answer received' : 'First text received' }}</span></li>
          </ol>
        </div>
      </details>
      <div v-if="$slots.evidence" class="chat-assistant-message"><span class="chat-speaker">{{ title }}</span><slot name="evidence" /></div>
      <template v-for="entry in entries" :key="entry.id">
        <div v-if="entry.kind === 'assistant' || entry.kind === 'error'" class="chat-assistant-message" :class="{ 'chat-error': entry.kind === 'error' }">
          <span class="chat-speaker">{{ title }}</span><ChatMessage :text="entry.text" />
        </div>
        <div v-else-if="entry.kind === 'tool' || entry.kind === 'step'" class="chat-activity" :class="{ 'chat-wait': entry.name === 'quota_wait' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="toolIcon(entry.name ?? '')" /></svg>
          <div><strong>{{ toolTitle(entry.name ?? entry.kind) }}</strong><p v-if="entry.text">{{ entry.text }}</p></div><span v-if="entry.state">{{ entry.state }}</span>
        </div>
      </template>
      <div v-if="!running && !queued && !entries.length && !error" class="chat-assistant-message"><span class="chat-speaker">{{ title }}</span><p>{{ emptyText ?? 'Same task. Same model. Press Send.' }}</p></div>
      <span v-if="running" class="chat-caret" aria-label="Streaming"></span>
      <div v-if="error && !entries.some(entry => entry.kind === 'error')" class="chat-assistant-message chat-error" role="alert"><span class="chat-speaker">{{ title }}</span><p>{{ error }}</p></div>
      <div v-if="result?.files?.length" class="chat-attachments">
        <a v-for="file in result.files" :key="file.path ?? file.id" :href="fileHref(file)" :download="file.path?.split('/').pop() ?? file.name">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6 3h8l4 4v14H6zm8 0v5h5M9 12h6m-6 4h6" /></svg>{{ file.path?.split('/').pop() ?? file.name }}
        </a>
        <p v-if="result.artifact_export">{{ result.artifact_export.note }}</p>
      </div>
    </div>
    <pre v-else-if="view === 'code'" class="chat-inspector">{{ code || 'No request code has been loaded.' }}</pre>
    <pre v-else-if="view === 'json'" class="chat-inspector" title="Opaque identifiers are redacted. The saved service response is unchanged.">{{ JSON.stringify(presentationJson(raw ?? result?.raw ?? { status, note: 'Press Send for actual response JSON.' }), null, 2) }}</pre>
    <div v-else class="chat-inspector chat-cost"><p>{{ tokenText }}</p><p>{{ result?.cost_usd == null ? 'Cost unknown. Verified rates are not configured.' : `$${result.cost_usd.toFixed(5)} estimated token cost` }}</p><p>{{ result?.usage_note }}</p><p>Wall clock includes tool work and visible quota waits. Authentication runs outside the request path.</p></div>
    <footer class="chat-metrics"><span>{{ (elapsed / 1000).toFixed(1) }} s</span><span>{{ subtitle?.includes('Nonstreaming') ? 'First text' : 'First token' }} {{ firstText == null ? running || queued ? 'pending' : 'unknown' : `${(firstText / 1000).toFixed(1)} s` }}</span><span>{{ calls }} tool calls</span><span>{{ result?.files?.length ?? 0 }} files</span><span>{{ tokenText }}</span><span v-if="result?.quota_retries" :title="result.usage_note">Final response usage</span><span>{{ result?.cost_usd == null ? 'Cost unknown' : `$${result.cost_usd.toFixed(5)}` }}</span></footer>
    <form class="chat-composer" @submit.prevent="emit('send')">
      <label><span>Fixed demo task</span><textarea :value="task" readonly rows="2" :aria-label="`${title} fixed demo task`" @keydown.enter.exact.prevent="!disabled && !running && emit('send')" /></label>
      <button v-if="running && stoppable" type="button" class="chat-send" :title="stopHint ?? 'Stop receiving this stream. Server-side work may finish.'" @click="emit('stop')">Stop</button>
      <button v-else type="submit" class="chat-send" :disabled="disabled || running || queued" :aria-label="`Send to ${title}`">{{ recorded ? 'Replay' : 'Send' }}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m5 12 7-7 7 7m-7-7v14" /></svg></button>
    </form>
  </article>
</template>
