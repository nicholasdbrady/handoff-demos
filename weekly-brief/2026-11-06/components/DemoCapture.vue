<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, onUnmounted, ref, watch } from 'vue'

type Asset = { path: string; kind: 'video' | 'image' | 'json' | 'text' | 'transcript'; caption: string; alt: string; poster?: string; prompt?: string; modelName?: string; label?: string }
type Manifest = {
  slug: string; title: string; status: 'ready' | 'partial' | 'unavailable'; captured_at: string
  environment: Record<string, unknown>; assets: Asset[]; metrics: Record<string, unknown>
  live: { supported: boolean; command?: string; typical_seconds?: number }; caveats: string[]
}
const props = defineProps<{ slug: string; assetMatch?: string; clipLabel?: string; noLive?: boolean; noMetrics?: boolean }>()
const manifest = ref<Manifest>()
const selected = ref(0)
const captureError = ref('')
const text = ref('')
const textError = ref('')
const mediaError = ref('')
const loading = ref(true)
const running = ref(false)
const liveEnabled = ref(false)
const liveError = ref('')
const liveResult = ref('')
let interval: ReturnType<typeof setInterval> | undefined
let alive = true
let textRevision = 0
const asset = computed(() => manifest.value?.assets[selected.value])
const player = ref<HTMLVideoElement>()
const promptChoices = computed(() => {
  const assets = manifest.value?.assets ?? []
  return assets.length > 1 && assets.every(item => item.kind === 'video' && item.prompt) ? assets : []
})
function choose(index: number, event: MouseEvent) {
  // Pointer users can advance with a clicker; keyboard users retain their place.
  if (event.detail > 0 && event.currentTarget instanceof HTMLElement) event.currentTarget.blur()
  if (index === selected.value) return
  player.value?.pause()
  selected.value = index
}
const displayedText = computed(() => text.value.replace(
  /\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?\b/g,
  value => new Date(value).toLocaleDateString('en-US', { timeZone: value.includes('T') ? 'America/Los_Angeles' : 'UTC', month: 'short', day: '2-digit' }),
))
const headlineMetrics = computed(() => Object.entries(manifest.value?.metrics ?? {}).filter(([, value]) => typeof value === 'number').slice(0, 4))
const viewPending = computed(() => Boolean(props.assetMatch && manifest.value && manifest.value.status !== 'unavailable' && !manifest.value.assets.length))
const htmlAsset = computed(() => asset.value?.kind === 'text' && /\.html?$/i.test(asset.value.path))
const isolatedHtml = computed(() => {
  if (!htmlAsset.value || !text.value) return ''
  const policy = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline' blob:; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; font-src data:; media-src data: blob:; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'\">"
  const document = new DOMParser().parseFromString(text.value, 'text/html')
  if (props.slug === 'kimi-k3-1-pro-benchmark') {
    document.querySelectorAll('.caption').forEach(node => node.remove())
    document.querySelectorAll('p').forEach(node => {
      if (/Three samples, not a leaderboard|Nov 9 catalog:|Reasoning tokens are already included/.test(node.textContent ?? '')) node.remove()
    })
  }
  return `${policy}${document.documentElement.outerHTML}`
})
const captured = computed(() => {
  const timestamp = manifest.value?.captured_at
  if (!timestamp) return 'Capture time not supplied'
  const date = new Date(timestamp)
  return Number.isNaN(date.valueOf()) ? 'Date unavailable' : date.toLocaleDateString('en-US', { timeZone: 'America/Los_Angeles', month: 'short', day: '2-digit' })
})
function assetUrl(path: string): string {
  const value = path.replaceAll('\\', '/').replace(/^\.?\//, '').replace(/^public\//, '')
  if (/^[a-z]+:/i.test(value) || value.split('/').includes('..')) throw new Error('Capture asset must be a local demo file.')
  const local = value.startsWith('demos/') ? value : `demos/${props.slug}/${value}`
  if (!local.startsWith(`demos/${props.slug}/`)) throw new Error('Capture asset is outside this demo.')
  return `${import.meta.env.BASE_URL}${local}`
}
function parseManifest(value: unknown): Manifest {
  if (!value || typeof value !== 'object') throw new Error('Invalid capture manifest.')
  const data = value as Record<string, unknown>
  if (data.slug !== props.slug || !['ready', 'partial', 'unavailable'].includes(String(data.status))
    || !Array.isArray(data.assets) || !Array.isArray(data.caveats)
    || !data.live || typeof data.live !== 'object' || typeof (data.live as Record<string, unknown>).supported !== 'boolean')
    throw new Error('Capture manifest does not match the demo contract.')
  if (typeof data.title !== 'string' || typeof data.captured_at !== 'string'
    || !data.environment || typeof data.environment !== 'object' || Array.isArray(data.environment)
    || !data.metrics || typeof data.metrics !== 'object' || Array.isArray(data.metrics))
    throw new Error('Capture manifest is missing title, timestamp, environment, or metrics.')
  const assets: Asset[] = []
  for (const item of data.assets) {
    if (!item || typeof item !== 'object' || typeof item.path !== 'string' || typeof item.caption !== 'string'
      || typeof item.alt !== 'string' || !['video', 'image', 'json', 'text', 'transcript'].includes(item.kind))
      throw new Error('Capture manifest contains an invalid asset.')
    assetUrl(item.path)
    if (item.poster !== undefined && typeof item.poster !== 'string') throw new Error('Capture poster must be a path.')
    if (item.prompt !== undefined && typeof item.prompt !== 'string') throw new Error('Capture prompt must be text.')
    if (item.model_name !== undefined && (typeof item.model_name !== 'string' || !item.model_name.trim()))
      throw new Error('Capture model name must be nonempty text.')
    if (item.label !== undefined && (typeof item.label !== 'string' || !item.label.trim()))
      throw new Error('Capture label must be nonempty text.')
    if (item.poster) assetUrl(item.poster)
    assets.push({ path: item.path, kind: item.kind, caption: item.caption, alt: item.alt, poster: item.poster, prompt: item.prompt,
      modelName: typeof item.model_name === 'string' ? item.model_name : undefined, label: typeof item.label === 'string' ? item.label : undefined })
  }
  if (!data.caveats.every(item => typeof item === 'string')) throw new Error('Capture caveats must be text.')
  const live = data.live as Record<string, unknown>
  const assetMatch = props.assetMatch?.toLowerCase()
  const status = String(data.status)
  if (status !== 'ready' && status !== 'partial' && status !== 'unavailable') throw new Error('Unknown demo status.')
  return {
    slug: props.slug, title: data.title,
    status, captured_at: data.captured_at,
    assets: assetMatch ? assets.filter(item => item.path.toLowerCase().includes(assetMatch)) : assets,
    environment: data.environment as Record<string, unknown>, metrics: data.metrics as Record<string, unknown>,
    live: { supported: live.supported === true, command: typeof live.command === 'string' ? live.command : undefined,
      typical_seconds: typeof live.typical_seconds === 'number' ? live.typical_seconds : undefined },
    caveats: data.caveats,
  }
}
async function refresh() {
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}demos/${props.slug}/manifest.json`, { cache: 'no-store' })
    // Vite serves its HTML fallback when an artifact has not arrived yet.
    if (response.status === 404 || response.headers.get('content-type')?.includes('text/html')) {
      manifest.value = undefined
      captureError.value = ''
      return
    }
    if (!response.ok) throw new Error(`Manifest returned HTTP ${response.status}.`)
    const data = parseManifest(await response.json())
    if (alive) {
      manifest.value = data
      captureError.value = ''
      if (selected.value >= data.assets.length) selected.value = 0
    }
  } catch (error) {
    if (alive) captureError.value = error instanceof Error ? error.message : String(error)
  } finally { if (alive) loading.value = false }
}
async function loadText() {
  const revision = ++textRevision
  text.value = ''
  textError.value = ''
  mediaError.value = ''
  if (!asset.value || ['video', 'image'].includes(asset.value.kind)) return
  try {
    const response = await fetch(assetUrl(asset.value.path), { cache: 'no-store' })
    if (!response.ok || (!htmlAsset.value && response.headers.get('content-type')?.includes('text/html')))
      throw new Error(`Capture file is unavailable (HTTP ${response.status}).`)
    const content = await response.text()
    if (content.length > 4_000_000) throw new Error('Capture file exceeds the 4 MB display limit.')
    if (alive && revision === textRevision) text.value = content
  } catch (error) {
    if (alive && revision === textRevision) textError.value = error instanceof Error ? error.message : String(error)
  }
}
async function runLive() {
  if (running.value) return
  running.value = true
  liveResult.value = ''
  liveError.value = ''
  try {
    const response = await fetch(`/demo-api/run/${props.slug}`, { method: 'POST', headers: { 'X-Demo-Client': 'slidev' } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || `Live execution returned HTTP ${response.status}.`)
    if (data.mode !== 'live') throw new Error('Adapter did not label this result as live.')
    liveResult.value = JSON.stringify(data.result, null, 2)
  } catch (error) {
    liveError.value = error instanceof Error ? error.message : String(error)
  } finally { running.value = false }
}
watch(asset, loadText)
// Slidev hides inactive slides; pause so a clip's audio never continues off-slide.
const root = ref<HTMLElement>()
const leaveObserver = typeof IntersectionObserver === 'undefined' ? undefined
  : new IntersectionObserver(entries => { if (entries.some(entry => !entry.isIntersecting)) player.value?.pause() })
const transitionObserver = typeof MutationObserver === 'undefined' ? undefined : new MutationObserver(entries => {
  for (const entry of entries) {
    if (entry.target instanceof Element && Array.from(entry.target.classList).some(name => name.endsWith('-leave-active')))
      player.value?.pause()
  }
})
watch(root, element => { if (element) leaveObserver?.observe(element) })
onMounted(async () => {
  const slide = root.value?.closest('.slidev-page')
  if (slide) transitionObserver?.observe(slide, { attributes: true, attributeFilter: ['class'] })
  await refresh()
  interval = setInterval(refresh, 30_000)
  if (props.noLive) return
  try {
    const response = await fetch('/demo-api/health', { headers: { 'X-Demo-Client': 'slidev' } })
    if (response.ok) liveEnabled.value = (await response.json()).live_enabled === true
  } catch { liveError.value = 'Local adapter is unavailable. Start demo_server.py to run live.' }
})
onBeforeUnmount(() => player.value?.pause())
onUnmounted(() => { alive = false; leaveObserver?.disconnect(); transitionObserver?.disconnect(); if (interval) clearInterval(interval) })
</script>

<template>
  <section ref="root" class="capture-demo" :aria-label="`${slug} demo`">
    <div class="capture-toolbar">
      <span class="badge">{{ viewPending ? 'Pending capture' : manifest?.status ?? (loading ? 'Loading capture' : 'Pending capture') }}</span>
      <span class="capture-time">{{ manifest && !viewPending ? `Captured ${captured}` : 'Waiting for this example’s capture' }}</span>
      <span v-if="promptChoices.length && clipLabel" class="capture-origin">{{ clipLabel }}</span>
      <button class="brief-button brief-secondary" @click="refresh">Refresh capture</button>
      <button v-if="manifest?.live.supported && !viewPending && !noLive" class="brief-button" :disabled="running || !liveEnabled" @click="runLive">
        {{ running ? 'Running live…' : 'Run live' }}
      </button>
    </div>
    <div v-if="headlineMetrics.length && !viewPending && !noMetrics" class="capture-metrics" aria-label="Captured measurements">
      <span v-for="[name, value] in headlineMetrics" :key="name"><strong>{{ value }}</strong> {{ name.replaceAll('_', ' ') }}</span>
    </div>
    <p v-if="captureError" role="alert" class="brief-error">{{ captureError }}</p>
    <div v-else-if="!manifest || viewPending" class="capture-empty">
      <svg viewBox="0 0 520 140" role="img" aria-label="Runner, capture, and slide waiting for captured evidence">
        <rect x="10" y="35" width="130" height="70" rx="12" /><path d="M140 70h50m-10-8 10 8-10 8" />
        <rect x="190" y="35" width="140" height="70" rx="12" /><path d="M330 70h50m-10-8 10 8-10 8" />
        <rect x="380" y="35" width="130" height="70" rx="12" />
        <text x="75" y="77">Runner</text><text x="260" y="77">Capture</text><text x="445" y="77">Slide</text>
      </svg>
      <h2>No captured result yet.</h2>
      <p>The explanation stays available. This panel will show real evidence when the demo lands.</p>
    </div>
    <template v-else>
      <div class="capture-body" :class="{ 'capture-prompted': asset?.prompt, 'capture-multi': promptChoices.length }">
        <div class="capture-media">
          <div v-if="promptChoices.length" class="capture-models" role="group" aria-label="Choose a model clip">
            <button v-for="(item, index) in promptChoices" :key="item.path" type="button" class="brief-button brief-secondary"
              :aria-pressed="index === selected" @click="choose(index, $event)">{{ item.modelName ?? item.caption }}</button>
          </div>
          <label v-else-if="manifest.assets.length > 1" class="capture-picker">Captured asset
            <select v-model="selected" aria-label="Captured asset">
              <option v-for="(item, index) in manifest.assets" :key="item.path" :value="index">{{ item.caption }}</option>
            </select>
          </label>
          <figure v-if="asset">
            <video v-if="asset.kind === 'video'" ref="player" :key="asset.path" controls preload="metadata" :src="assetUrl(asset.path)" :aria-label="asset.alt"
                          :poster="asset.poster ? assetUrl(asset.poster) : undefined"
                          @error="mediaError = 'Captured video could not load. Refresh the capture or inspect the demo files.'" />
            <img v-else-if="asset.kind === 'image'" :src="assetUrl(asset.path)" :alt="asset.alt"
              @error="mediaError = 'Captured image could not load. Refresh the capture or inspect the demo files.'" />
            <p v-else-if="textError" role="alert" class="brief-error">{{ textError }}</p>
            <iframe v-else-if="htmlAsset && isolatedHtml" class="capture-artifact" :srcdoc="isolatedHtml"
              sandbox="allow-scripts" referrerpolicy="no-referrer" :title="asset.alt"
              allow="camera 'none'; microphone 'none'; geolocation 'none'; payment 'none'; clipboard-read 'none'; clipboard-write 'none'" />
            <pre v-else class="capture-transcript" tabindex="0">{{ displayedText || 'Loading captured text…' }}</pre>
            <p v-if="mediaError" role="alert" class="brief-error">{{ mediaError }}</p>
          </figure>
          <div v-else class="capture-empty">
            <h2>{{ manifest.status === 'unavailable' ? 'Demo unavailable' : 'No captured assets' }}</h2>
            <p>Use the source walkthrough. No recorded result is being substituted.</p>
          </div>
        </div>
        <aside class="capture-details">
          <template v-if="asset?.prompt">
            <p v-if="!promptChoices.length && (asset.label ?? clipLabel)" class="capture-clip-label">{{ asset.label ?? clipLabel }}</p>
            <h2>Prompt<span v-if="promptChoices.length && asset.label" class="capture-scene"> · {{ asset.label }}</span></h2>
            <blockquote class="capture-prompt">{{ asset.prompt }}</blockquote>
          </template>
          <h2 v-else>{{ manifest.title }}</h2>
        </aside>
      </div>
    </template>
    <div v-if="running || liveResult || liveError" class="capture-live" aria-live="polite">
      <span v-if="running" class="live-signal" data-live-state="live">Live runner · up to 350 seconds</span>
      <p v-if="liveError" role="alert" class="brief-error">Live failed: {{ liveError }}</p>
      <details v-if="liveResult" open><summary>Live result · not a captured replay</summary><pre tabindex="0">{{ liveResult }}</pre></details>
    </div>
  </section>
</template>
