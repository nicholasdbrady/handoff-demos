<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { streamDemo, type LiveResult } from '../demo-stream'
import { appendEvent, finishTranscript, recordedTranscript, type ChatEntry } from '../chat-transcript'

const mode = ref('recorded')
const task = ref('Loading the shared recipe task...')
const status = ref('Checking local adapter...')
const live = ref(false)
const busy = ref(false)
const now = ref(0)
const lanes = reactive([
  { id: 'default', title: 'Default runtime', avatar: 'P', subtitle: 'Prompt agent · no tools', result: null as LiveResult | null, error: '', started: 0, ended: 0, running: false, queued: false, entries: [] as ChatEntry[] },
  { id: 'copilot', title: 'Copilot harness', avatar: 'C', subtitle: 'Tools + skill + workspace', result: null as LiveResult | null, error: '', started: 0, ended: 0, running: false, queued: false, entries: [] as ChatEntry[] },
])
let ticker: ReturnType<typeof setInterval> | undefined
let active: AbortController | undefined
watch(mode, () => { for (const lane of lanes) { lane.result = null; lane.entries = []; lane.error = ''; lane.ended = 0 } })
async function run(selected?: string) {
  if (busy.value) return
  busy.value = true
  const selectedLanes = lanes.filter(lane => !selected || lane.id === selected)
  for (const lane of selectedLanes) { lane.queued = true; lane.started = performance.now(); lane.result = null; lane.entries = []; lane.error = ''; lane.ended = 0 }
  ticker = setInterval(() => { now.value = performance.now() }, 100)
  for (const lane of selectedLanes) {
    lane.queued = false; lane.started = performance.now(); now.value = lane.started; lane.running = true
    active = new AbortController()
    try {
      if (mode.value === 'recorded') {
        const response = await fetch(`/recordings/${lane.id}.json`)
        if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('No recorded run has been captured for this lane.')
        const result: LiveResult = await response.json()
        lane.result = result; lane.entries = recordedTranscript(result)
      } else {
        lane.result = await streamDemo(lane.id, event => appendEvent(lane.entries, event, performance.now() - lane.started), active.signal)
        finishTranscript(lane.entries, lane.result.text)
      }
    } catch (error) {
      lane.error = active.signal.aborted
        ? 'Stream stopped. Server-side work may finish; wait for the model slot before sending again.'
        : error instanceof Error ? error.message : 'Request failed.'
    } finally { lane.ended = performance.now(); lane.running = false }
    if (active.signal.aborted) { for (const queued of selectedLanes) queued.queued = false; break }
  }
  clearInterval(ticker); active = undefined; busy.value = false
}
function elapsed(lane: typeof lanes[number]) {
  return lane.running || lane.queued ? Math.max(0, now.value - lane.started) : lane.result?.elapsed_ms ?? (lane.ended ? lane.ended - lane.started : 0)
}
function code(lane: typeof lanes[number]) {
  return `client = project.get_openai_client(\n    agent_name="${lane.id === 'copilot' ? 'livestream-recipe-copilot-1102' : 'livestream-recipe-default-1102'}"\n)\nconversation = client.conversations.create()\nstream = client.responses.create(\n    conversation=conversation.id,\n    input=SHARED_RECIPE_TASK,\n    stream=True,\n)\nfor event in stream:\n    handle(event)`
}
onMounted(async () => {
  try {
    const response = await fetch('/task.json')
    if (!response.ok) throw new Error('Shared task unavailable.')
    task.value = (await response.json()).prompt
    const connection = await fetch('/demo-api/status', { headers: { 'X-Demo-Client': 'slidev' } })
    if (!connection.ok) throw new Error('Local adapter unavailable.')
    const body = await connection.json()
    live.value = body.ready
    status.value = body.message
  } catch (error) { status.value = error instanceof Error ? error.message : 'Adapter unavailable.' }
})
onUnmounted(() => { clearInterval(ticker); active?.abort() })
</script>

<template>
  <section class="chat-comparison" aria-label="Recipe factory runtime comparison" @click.stop @keydown.stop>
    <div class="chat-controls">
      <p>One task. One model. A different harness.</p>
      <label>Mode <select v-model="mode" :disabled="busy"><option value="live" :disabled="!live">Live · your Foundry project</option><option value="recorded">SYNTHETIC · offline fixture</option></select></label>
      <button class="chat-both" :disabled="busy || (mode === 'live' && !live)" @click="run()">{{ busy ? 'Sending in series…' : 'Send to both' }}</button>
    </div>
    <div class="chat-windows">
      <ChatLane v-for="lane in lanes" :key="lane.id" :title="lane.title" :subtitle="lane.subtitle" :avatar="lane.avatar"
        :task="task" :entries="lane.entries" :result="lane.result" :error="lane.error" :running="lane.running" :queued="lane.queued"
        :recorded="mode === 'recorded'" :disabled="busy || (mode === 'live' && !live)" :elapsed="elapsed(lane)" :code="code(lane)"
        :stoppable="true" @send="run(lane.id)" @stop="active?.abort()" />
    </div>
    <p class="chat-boundary">{{ status }} Bundled replay is synthetic, not measured service output. Live failures stay visible.</p>
  </section>
</template>
