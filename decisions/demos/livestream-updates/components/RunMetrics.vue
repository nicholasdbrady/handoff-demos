<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import type { NativeResult } from '../demo-api'

const props = defineProps<{ busy: boolean; result?: NativeResult; pairs?: number; processed?: number }>()
const elapsed = ref<number>()
let started: number | undefined
let ticker: ReturnType<typeof setInterval> | undefined
watch(() => props.busy, busy => {
  clearInterval(ticker)
  if (busy) {
    const start = performance.now()
    started = start
    elapsed.value = 0
    ticker = setInterval(() => { elapsed.value = performance.now() - start }, 100)
  }
  else if (started !== undefined) {
    elapsed.value = performance.now() - started
    started = undefined
  }
}, { immediate: true, flush: 'sync' })
watch(() => props.result, result => {
  if (!props.busy && !result) elapsed.value = undefined
}, { flush: 'sync' })
onUnmounted(() => clearInterval(ticker))
function duration(ms: number | undefined | null) {
  if (ms == null) return '— s'
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`
}
const clock = computed(() => duration(elapsed.value))
const apiTime = computed(() => !props.busy && props.result?.elapsed_ms != null
  ? `${props.pairs ? 'API calls total' : 'API round trip'} ${duration(props.result.elapsed_ms)}` : '')
const throughput = computed(() => props.pairs && elapsed.value && props.processed && props.result?.mode !== 'rehearsal'
  ? `${(props.processed * 1000 / elapsed.value).toFixed(1)} pairs / s` : '')
const cost = computed(() => {
  if (props.busy || !props.result) return 'Cost after run'
  if (props.result.mode === 'rehearsal') return 'Rehearsal · no billable call'
  const usd = props.result.cost_usd
  if (usd == null) return 'Cost unavailable'
  const amount = usd * 1000 / (props.pairs ?? 1)
  return `≈ $${amount >= 1 ? amount.toFixed(2) : amount.toPrecision(2)} / 1K ${props.pairs ? 'pairs' : 'runs'}`
})
</script>

<template>
  <div class="run-metrics" aria-label="Run timing and estimated cost">
    <output class="run-clock" aria-label="Total elapsed time" title="Full browser wait, including local adapter, authentication, queueing, and provider request.">{{ clock }}</output>
    <span v-if="elapsed !== undefined" class="timing-label">Total elapsed</span>
    <span v-if="apiTime" class="api-timing" title="Adapter-measured provider call including network time; excludes work before that call and is not pure model inference time.">{{ apiTime }}</span>
    <span v-if="throughput">{{ throughput }}</span>
    <span :title="result?.cost_note ?? 'Estimate for 1,000 calls with the same token usage; not an invoice.'">{{ cost }}</span>
  </div>
</template>
