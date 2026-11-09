<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type Effort = 'none' | 'low' | 'high'
type Metric = { requested_reasoning_effort: Effort; total_tokens: number; reasoning_tokens: number; latency_ms: number }
const efforts: Effort[] = ['none', 'low', 'high']
const selected = ref<Effort>('none')
const metrics = ref<Metric[]>([])
const scenes = ref<Partial<Record<Effort, string>>>({})
const timestamp = ref('')
const prompt = ref('')
const error = ref('')
const loading = ref(true)
const liveEnabled = ref(false)
const running = ref(false)
const liveError = ref('')
const liveResult = ref('')
const documentHtml = computed(() => scenes.value[selected.value] ?? '')
const root = `${import.meta.env.BASE_URL}demos/kimi-k3-1-pro/`

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid Kimi capture object.')
  return value as Record<string, unknown>
}
function localPath(path: string): string {
  const clean = path.replace(/^\/?demos\/kimi-k3-1-pro\//, '')
  if (clean.includes('..') || /^[a-z]+:/i.test(clean) || clean.startsWith('/')) throw new Error('Scene asset is outside the capture.')
  return root + clean
}
function isolate(source: string, runtime: string): string {
  const tree = new DOMParser().parseFromString(source, 'text/html')
  const external = Array.from(tree.querySelectorAll<HTMLScriptElement>('script[src]'))
  if (external.length !== 1 || external[0].getAttribute('src') !== './vendor/three.min.js')
    throw new Error('The captured scene has an unexpected script dependency.')
  if (tree.querySelector('iframe,object,embed,base,form,link')) throw new Error('The captured scene contains an unsupported active element.')
  tree.querySelectorAll('meta[http-equiv]').forEach(node => node.remove())
  const policy = tree.createElement('meta')
  policy.httpEquiv = 'Content-Security-Policy'
  policy.content = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; object-src 'none'"
  tree.head.prepend(policy)
  external[0].removeAttribute('src')
  external[0].textContent = runtime.replace(/<\/script/gi, '<\\/script')
  return '<!doctype html>' + tree.documentElement.outerHTML
}
async function response(path: string): Promise<Response> {
  const result = await fetch(path, { cache: 'no-store' })
  if (!result.ok) throw new Error(`Capture returned HTTP ${result.status}: ${path.split('/').at(-1)}`)
  return result
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const manifestResponse = await response(root + 'manifest.json')
    if (manifestResponse.headers.get('content-type')?.includes('text/html')) throw new Error('Kimi capture is pending.')
    const manifest = object(await manifestResponse.json())
    const measurements = object(manifest.metrics)
    if (!Array.isArray(measurements.scenes) || !Array.isArray(manifest.assets)) throw new Error('The scene comparison is not captured yet.')
    metrics.value = measurements.scenes.map(value => {
      const data = object(value)
      const effort = data.requested_reasoning_effort
      if ((effort !== 'none' && effort !== 'low' && effort !== 'high') || typeof data.total_tokens !== 'number'
        || typeof data.reasoning_tokens !== 'number' || typeof data.latency_ms !== 'number')
        throw new Error('Invalid captured scene measurements.')
      return { requested_reasoning_effort: effort, total_tokens: data.total_tokens,
        reasoning_tokens: data.reasoning_tokens, latency_ms: data.latency_ms }
    })
    const runtime = await (await response(root + 'vendor/three.min.js')).text()
    const assets = manifest.assets.map(object)
    for (const effort of efforts) {
      const asset = assets.find(item => item.kind === 'text' && typeof item.caption === 'string' && item.caption.includes(`${effort}-effort generated HTML`))
      if (!asset || typeof asset.path !== 'string') throw new Error(`Missing ${effort} scene capture.`)
      scenes.value[effort] = isolate(await (await response(localPath(asset.path))).text(), runtime)
    }
    const captures = object(await (await response(root + 'recorded-results.json')).json())
    if (!Array.isArray(captures.scenes) || !captures.scenes.length) throw new Error('Missing exact scene prompt.')
    const question = object(captures.scenes[0]).question
    if (typeof question !== 'string') throw new Error('Missing exact scene prompt.')
    prompt.value = question
    if (typeof manifest.captured_at !== 'string') throw new Error('Missing capture timestamp.')
    if (Number.isNaN(new Date(manifest.captured_at).valueOf())) throw new Error('Invalid capture timestamp.')
    timestamp.value = new Date(manifest.captured_at).toLocaleString('en-US', { timeZone: 'America/Los_Angeles', timeZoneName: 'short' })
    const health = await fetch('/demo-api/health', { headers: { 'X-Demo-Client': 'slidev' } })
    if (health.ok) liveEnabled.value = (await health.json()).live_enabled === true
  } catch (cause) { error.value = cause instanceof Error ? cause.message : String(cause) }
  finally { loading.value = false }
}
async function runLive() {
  running.value = true
  liveError.value = ''
  liveResult.value = ''
  try {
    const result = await fetch('/demo-api/run/kimi-k3-1-pro', { method: 'POST', headers: { 'X-Demo-Client': 'slidev' } })
    const data = await result.json()
    if (!result.ok) throw new Error(data.detail || `Live runner returned HTTP ${result.status}`)
    if (data.mode !== 'live') throw new Error('The adapter did not identify a live result.')
    liveResult.value = JSON.stringify(data.result, null, 2)
  } catch (cause) { liveError.value = cause instanceof Error ? cause.message : String(cause) }
  finally { running.value = false }
}
onMounted(load)
</script>

<template>
  <section class="kimi-comparison" aria-label="Kimi captured three.js comparison">
    <div class="capture-toolbar">
      <span class="badge">{{ loading ? 'Loading capture' : error ? 'Capture unavailable' : 'Captured model output' }}</span><span class="capture-time">{{ timestamp }}</span>
      <button class="brief-button brief-secondary" @click="load">Refresh capture</button>
      <button class="brief-button" :disabled="!liveEnabled || running || loading || Boolean(error)"
        :title="liveEnabled ? 'Run a new none-effort sculpture request' : 'Start demo_server.py and enable SLIDEV_ENABLE_LIVE after configuring Kimi.'"
        @click="runLive">{{ running ? 'Running live…' : liveEnabled ? 'Run sculpture live' : 'Live disabled' }}</button>
    </div>
    <p v-if="loading">Loading recorded scenes…</p>
    <p v-else-if="error" role="alert" class="brief-error">{{ error }}</p>
    <template v-else>
      <div class="kimi-stage">
        <div>
          <div class="kimi-efforts" aria-label="Captured reasoning setting">
            <button v-for="effort in efforts" :key="effort" class="brief-button brief-secondary" :aria-pressed="selected === effort"
              @click="selected = effort">{{ effort }}</button>
            <span>Same prompt · 12,000 completion-token cap</span>
          </div>
          <iframe :key="selected" :srcdoc="documentHtml" sandbox="allow-scripts" referrerpolicy="no-referrer"
            :title="`Captured ${selected}-effort Kimi sculpture`" class="kimi-artifact"
            allow="camera 'none'; microphone 'none'; geolocation 'none'; payment 'none'; clipboard-read 'none'; clipboard-write 'none'" />
        </div>
        <aside>
          <h2>Tokens and time.</h2>
          <table class="kimi-metrics">
            <thead><tr><th>Effort</th><th>Total tokens</th><th>Seconds</th></tr></thead>
            <tbody><tr v-for="row in metrics" :key="row.requested_reasoning_effort">
              <th>{{ row.requested_reasoning_effort }}</th><td>{{ row.total_tokens.toLocaleString('en-US') }}</td><td>{{ (row.latency_ms / 1000).toFixed(2) }}</td>
            </tr></tbody>
          </table>
          <div class="demo-limits" aria-label="Demo limits">
            <p>Reasoning tokens are included in output tokens.</p>
            <p>One sample per reasoning setting; not a quality ranking.</p>
            <p>Nov 9 catalog: GA; brief: preview. Cutoff status is unverified.</p>
          </div>
        </aside>
      </div>
      <details class="kimi-prompt"><summary>Exact shared prompt</summary><pre tabindex="0">{{ prompt }}</pre></details>
    </template>
    <div v-if="running || liveError || liveResult" class="capture-live" aria-live="polite">
      <span v-if="running" class="live-signal" data-live-state="live">Live sculpture request · none effort</span>
      <p v-if="liveError" role="alert" class="brief-error">{{ liveError }}</p>
      <details v-if="liveResult" open><summary>Live result · inspect generated code before executing</summary><pre tabindex="0">{{ liveResult }}</pre></details>
    </div>
  </section>
</template>
