<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { streamDemo, type LiveResult } from '../demo-stream'
import { appendEvent, finishTranscript, recordedTranscript, type ChatEntry } from '../chat-transcript'

const props = defineProps<{ focus: 'sdk' | 'maf' }>()
const mode = ref('recorded')
const task = ref('Loading the shared recipe task...')
const taskReady = ref(false)
const busy = ref(false)
const now = ref(0)
const status = ref('Synthetic fixture only. Hosted runtime and deployment are not included in this repository.')
const lanes = reactive([
  { id: props.focus === 'sdk' ? 'copilot' : 'sdk', title: props.focus === 'sdk' ? 'Copilot harness' : 'Copilot SDK hosted', avatar: props.focus === 'sdk' ? 'C' : 'S', subtitle: props.focus === 'sdk' ? 'Managed prompt agent' : 'Code-first Copilot runtime', result: null as LiveResult | null, error: '', running: false, queued: false, started: 0, ended: 0, entries: [] as ChatEntry[] },
  { id: props.focus, title: props.focus === 'sdk' ? 'Copilot SDK hosted' : 'Agent Framework', avatar: props.focus === 'sdk' ? 'S' : 'A', subtitle: props.focus === 'sdk' ? 'Code-first Copilot runtime' : 'Custom orchestration + tool policy', result: null as LiveResult | null, error: '', running: false, queued: false, started: 0, ended: 0, entries: [] as ChatEntry[] },
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
    lane.queued = false; lane.running = true; lane.started = performance.now(); now.value = lane.started
    active = new AbortController()
    try {
      if (mode.value === 'recorded') {
        const response = await fetch(lane.id === 'copilot' ? '/recordings/copilot.json' : `/recordings/hosted-${lane.id}.json`)
        if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('No recorded run has been captured for this lane.')
        const result: LiveResult = await response.json()
        lane.result = result; lane.entries = recordedTranscript(result)
      } else {
        lane.result = await streamDemo(lane.id === 'copilot' ? 'copilot' : `hosted/${lane.id}`,
          event => appendEvent(lane.entries, event, performance.now() - lane.started), active.signal)
        finishTranscript(lane.entries, lane.result.text)
      }
    } catch (error) {
      lane.error = active.signal.aborted
        ? 'Stream stopped. Server-side work may finish; wait for the model slot before sending again.'
        : error instanceof Error ? error.message : 'The hosted demo failed.'
    } finally { lane.ended = performance.now(); lane.running = false }
    if (active.signal.aborted) { for (const queued of selectedLanes) queued.queued = false; break }
  }
  clearInterval(ticker); active = undefined; busy.value = false
}
function elapsed(lane: typeof lanes[number]) {
  return lane.running || lane.queued ? Math.max(0, now.value - lane.started) : lane.result?.elapsed_ms ?? (lane.ended ? lane.ended - lane.started : 0)
}
function code(id: string) {
  return id === 'copilot'
    ? 'client = project.get_openai_client(agent_name=COPILOT_AGENT)\nconversation = client.conversations.create()\nstream = client.responses.create(\n    conversation=conversation.id,\n    input=SHARED_RECIPE_TASK, stream=True,\n)'
    : `# ${id === 'sdk' ? 'Copilot SDK hosted runtime' : 'Custom Agent Framework runtime'}\n# Server-side hosted/lane_runner.py\nfor event in stream_lane("${id}"):\n    yield json.dumps(event) + "\\n"\n\n# Foundry Responses endpoint; Entra token stays server-side.\n# Runtime tools, approvals and lifecycle are application code.`
}
onMounted(async () => {
  try {
    const response = await fetch('/task.json')
    if (!response.ok) throw new Error('Shared task unavailable.')
    task.value = (await response.json()).prompt
    taskReady.value = true
  } catch (error) { status.value = error instanceof Error ? error.message : 'Shared task unavailable.' }
})
onUnmounted(() => { clearInterval(ticker); active?.abort() })
</script>

<template>
  <section class="chat-comparison" aria-label="Code-first harness comparison" @click.stop @keydown.stop>
    <div class="chat-controls">
      <p>Same task and model. More control means owning more runtime.</p>
      <label>Mode <select v-model="mode" :disabled="busy"><option value="recorded">SYNTHETIC · offline fixture</option></select></label>
      <button class="chat-both" :disabled="busy || !taskReady" @click="run()">{{ busy ? 'Sending in series…' : 'Send to both' }}</button>
    </div>
    <div class="chat-windows">
      <ChatLane v-for="lane in lanes" :key="lane.id" :title="lane.title" :subtitle="lane.subtitle" :avatar="lane.avatar"
        :task="task" :entries="lane.entries" :result="lane.result" :error="lane.error" :running="lane.running" :queued="lane.queued"
        :recorded="mode === 'recorded'" :disabled="busy || !taskReady" :elapsed="elapsed(lane)" :code="code(lane.id)" :stoppable="true"
        @send="run(lane.id)" @stop="active?.abort()" />
    </div>
    <p class="chat-boundary">{{ status }} This illustrates the interface, not hosted execution or a performance comparison.</p>
  </section>
</template>
