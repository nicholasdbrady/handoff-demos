<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import light from '../public/harness-light.svg?raw'
import dark from '../public/harness-dark.svg?raw'

function themeSvg(svg: string, theme: string) {
  return svg.replace(/id="([^"]+)"/g, `id="${theme}-$1"`).replace(/url\(#([^)]+)\)/g, `url(#${theme}-$1)`)
}
const lightSvg = themeSvg(light, 'light')
const darkSvg = themeSvg(dark, 'dark')
const props = defineProps<{ active: boolean }>()
const root = ref<HTMLElement>()
const paused = ref(false)
const elapsed = ref(0)
const label = ref('Input arrives')
const reduced = ref(false)
const active = computed(() => props.active)
const print = ref(false)
const alt = 'Inside a dashed harness, a clockwise LLM, tool, workspace and context loop returns through harness policy, checkpoint and progress checks: the first turn continues, and the second completes before a response exits right.'
type Phase = { id: string; start: number; end: number; turn: number; route: string; from: number; to: number; station?: string; checks?: number; decision?: string; label: string; response?: boolean }
const phases: Phase[] = []
function phase(id: string, seconds: number, state: Omit<Phase, 'id' | 'start' | 'end'>) {
  const start = phases.at(-1)?.end ?? 0
  phases.push({ id, start, end: start + seconds, ...state })
}
let frame = 0
let previous = 0
let media: MediaQueryList
const routes: Record<string, string> = {
  input: 'M 225 660 H 514 Q 526 660 526 648 V 642 H 640',
  lap: 'M 640 642 H 568 Q 556 642 556 630 V 620 A 185 185 0 1 1 724 620 V 630 Q 724 642 712 642 H 640',
  check: 'M 640 642 V 555',
  response: 'M 640 642 H 764 Q 776 642 776 654 Q 776 660 790 660 H 1075',
}
const paths: Record<string, SVGPathElement> = {}
function initialize() {
  for (const [name, d] of Object.entries(routes)) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    path.setAttribute('d', d)
    paths[name] = path
  }
  const lap = paths.lap
  const length = lap.getTotalLength()
  const stops = [0]
  for (const [x, y] of [[455, 455], [640, 270], [825, 455]]) {
    let nearest = 0, distance = Infinity
    for (let d = 0; d <= length; d += 0.5) {
      const p = lap.getPointAtLength(d)
      const error = Math.hypot(p.x - x, p.y - y)
      if (error < distance) { distance = error; nearest = d / length }
    }
    stops.push(nearest)
  }
  stops.push(1)
  phase('input', 2, { route: 'input', from: 0, to: 1, station: 'llm', label: 'Input arrives', turn: 1 })
  phase('decide', 1.2, { route: 'lap', from: 0, to: 0, station: 'llm', label: 'Tool call', turn: 1 })
  for (const turn of [1, 2]) {
    const stations = ['tool', 'workspace', 'context', 'llm']
    const labels = ['Tool dispatch', 'Tool execution', 'Result into context', 'Model continues']
    stations.forEach((station, i) => {
      phase(`turn-${turn}-${station}`, 1.6, { turn, route: 'lap', from: stops[i], to: stops[i + 1], station, label: labels[i] })
      if (station !== 'llm') phase(`turn-${turn}-${station}-hold`, 0.6, { turn, route: 'lap', from: stops[i + 1], to: stops[i + 1], station, label: labels[i] })
    })
    const check = { turn, route: 'check', from: 1, to: 1 }
    const decision = turn === 1 ? 'Continue' : 'Complete'
    phase(`turn-${turn}-boundary`, 0.8, { ...check, from: 0, checks: 0, label: 'Harness turn boundary' })
    phase(`turn-${turn}-policy`, 1.2, { ...check, checks: 1, label: 'Configured policy + limits' })
    phase(`turn-${turn}-checkpoint`, 1.2, { ...check, checks: 2, label: 'Checkpoint state' })
    phase(`turn-${turn}-progress`, 1.4, { ...check, checks: 3, label: turn === 1 ? 'Progress made; not complete' : 'Completion criteria satisfied' })
    phase(`turn-${turn}-decision`, 1.6, { ...check, checks: 4, decision, label: `${decision}: ${turn === 1 ? 'another bounded turn' : 'response permitted'}` })
    phase(`turn-${turn}-return`, 0.8, { ...check, to: 0, checks: 4, decision, station: 'llm', label: turn === 1 ? 'Continue into turn 2' : 'Release response' })
  }
  phase('response', 2.4, { turn: 2, route: 'response', from: 0, to: 1, checks: 4, decision: 'Complete', response: true, label: 'Response delivered' })
  phase('hold', 4, { turn: 2, route: 'response', from: 1, to: 1, checks: 4, decision: 'Complete', response: true, label: 'Complete' })
}
const duration = computed(() => phases.at(-1)?.end ?? 40)
function paint() {
  const current = phases.find(p => elapsed.value < p.end) ?? phases.at(-1)
  if (!current || !root.value) return
  label.value = `Turn ${current.turn} · ${current.label}`
  root.value.dataset.phase = current.id
  root.value.dataset.elapsed = elapsed.value.toFixed(3)
  const path = paths[current.route]
  const fraction = Math.max(0, Math.min(1, (elapsed.value - current.start) / (current.end - current.start)))
  const point = path.getPointAtLength(path.getTotalLength() * (current.from + (current.to - current.from) * fraction))
  root.value.querySelectorAll('svg').forEach(svg => {
    const token = svg.querySelector<SVGCircleElement>('.turn-token')
    if (token) {
      token.removeAttribute('hidden')
      token.setAttribute('display', reduced.value ? 'none' : 'inline')
      token.setAttribute('cx', String(point.x)); token.setAttribute('cy', String(point.y))
    }
    svg.querySelectorAll<SVGElement>('[data-station]').forEach(node => {
      node.setAttribute('stroke-width', node.dataset.station === current.station ? '3' : node.dataset.station === 'llm' ? '4' : '2')
    })
    svg.querySelectorAll<SVGGElement>('[data-check]').forEach((row, i) => {
      const state = (current.checks ?? 0) > i + 1 ? 'done' : current.checks === i + 1 ? 'active' : 'pending'
      row.dataset.state = state
      row.setAttribute('opacity', state === 'pending' ? '.72' : '1')
      row.querySelector('.check-mark')?.setAttribute('visibility', state === 'pending' ? 'hidden' : 'visible')
      row.querySelector('text')?.setAttribute('font-weight', state === 'active' ? '750' : '550')
    })
    const set = (selector: string, text: string) => { const node = svg.querySelector(selector); if (node) node.textContent = text }
    set('[data-check="checkpoint"] text', (current.checks ?? 0) >= 2 ? 'State saved' : 'Checkpoint')
    set('[data-check="progress"] text', (current.checks ?? 0) >= 3 ? current.turn === 1 ? 'Progress made' : 'Goal met' : 'Progress / goal')
    set('[id$="-turn-heading"]', `Turn ${current.turn}`)
    set('[id$="-turn-decision"]', current.decision ?? (current.checks === undefined ? current.label : 'Checking'))
    const output = svg.querySelector('.turn-output')
    output?.setAttribute('data-active', String(!!current.response))
    output?.setAttribute('stroke', current.response ? svg.querySelector('.orbit-model')?.getAttribute('stroke') ?? '' : svg.querySelector('.orbit-boundary')?.getAttribute('stroke') ?? '')
  })
}
function stop() { cancelAnimationFrame(frame); frame = 0; previous = 0 }
function tick(now: number) {
  if (!active.value || print.value || paused.value || document.hidden) { stop(); return }
  if (previous) elapsed.value = Math.min(duration.value, elapsed.value + (now - previous) / 1000)
  previous = now
  paint()
  if (elapsed.value < duration.value) frame = requestAnimationFrame(tick)
  else stop()
}
function sync() {
  stop()
  if (active.value && !print.value && !paused.value && !document.hidden && elapsed.value < duration.value) frame = requestAnimationFrame(tick)
}
function replay() { elapsed.value = 0; paused.value = false; paint(); sync() }
function motionChange() { reduced.value = media.matches; paint() }
watch(active, (isActive, wasActive) => { if (isActive && !wasActive) replay(); else sync() })
watch([paused, print], sync)
onMounted(() => {
  print.value = new URLSearchParams(location.search).has('print') || location.pathname.includes('/export')
  initialize()
  media = matchMedia('(prefers-reduced-motion: reduce)')
  reduced.value = media.matches
  media.addEventListener('change', motionChange)
  document.addEventListener('visibilitychange', sync)
  paint(); sync()
})
onUnmounted(() => {
  stop()
  media?.removeEventListener('change', motionChange)
  document.removeEventListener('visibilitychange', sync)
})
</script>

<template>
  <div ref="root" class="harness-orbit" :data-paused="paused">
    <div v-if="!print" class="orbit-animation" role="img" :aria-label="alt">
      <div class="orbit-light" v-html="lightSvg" />
      <div class="orbit-dark" v-html="darkSvg" />
    </div>
    <div class="orbit-static" :class="{ 'export-visible': print }">
      <img class="diagram diagram-light" src="/harness-light.png" :alt="alt">
      <img class="diagram diagram-dark" src="/harness-dark.png" :alt="alt">
    </div>
    <div v-if="!print" class="orbit-controls">
      <button type="button" @click="replay">Replay</button>
      <button type="button" :disabled="elapsed >= duration" @click="paused = !paused">{{ paused ? 'Resume' : 'Pause' }}</button>
      <span role="status" aria-live="polite">{{ label }}{{ reduced ? ' · reduced motion' : '' }}</span>
    </div>
  </div>
</template>

<style scoped>
.orbit-animation { height: 465px; }
.orbit-animation > div { height: 100%; }
.orbit-animation :deep(svg) { display: block; width: 100%; height: 100%; }
.orbit-dark { display: none; }
.orbit-static { display: none; }
.orbit-static.export-visible { display: block; }
:global(html.dark) .orbit-light { display: none; }
:global(html.dark) .orbit-dark { display: block; }
.orbit-controls { display: flex; align-items: center; gap: 16px; margin-top: 8px; font-size: 16px; }
.orbit-controls button { border: 1px solid var(--accent); border-radius: 8px; padding: 5px 12px; background: var(--surface-raised); color: var(--ink); }
.orbit-controls button:disabled { opacity: .6; }
@media print { .orbit-controls, .orbit-animation { display: none; } .orbit-static { display: block; } }
</style>
