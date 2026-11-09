<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const stages = [
  'Traces',
  'Human-reviewed outcomes',
  'Isolated tool tests',
  'Held-out regression',
  'Canary promotion',
]

const activeIndex = ref(0)
const playing = ref(false)
const reducedMotion = ref(false)
const activeStage = computed(() => stages[activeIndex.value])

let timer: number | undefined
let motionPreference: MediaQueryList | undefined

function stopTimer() {
  if (timer !== undefined) {
    window.clearInterval(timer)
    timer = undefined
  }
}

function syncTimer() {
  stopTimer()
  if (!playing.value || reducedMotion.value) return

  timer = window.setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % stages.length
  }, 3200)
}

function selectStage(index: number) {
  activeIndex.value = index
}

function togglePlayback() {
  if (reducedMotion.value) return
  playing.value = !playing.value
  syncTimer()
}

function handleMotionPreference(event: MediaQueryListEvent) {
  reducedMotion.value = event.matches
  if (event.matches) playing.value = false
  syncTimer()
}

onMounted(() => {
  motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = motionPreference.matches
  playing.value = !reducedMotion.value
  motionPreference.addEventListener('change', handleMotionPreference)
  syncTimer()
})

onUnmounted(() => {
  stopTimer()
  motionPreference?.removeEventListener('change', handleMotionPreference)
})
</script>

<template>
  <section class="improvement-loop" aria-labelledby="improvement-loop-title">
    <header class="loop-header">
      <div>
        <h2 id="improvement-loop-title">A measured improvement loop</h2>
        <p class="loop-pattern-label">Implementation pattern</p>
      </div>
      <span class="loop-preview-label">Agent Optimizer preview</span>
    </header>

    <div class="loop-diagram">
      <svg
        class="loop-track"
        viewBox="0 0 1000 72"
        preserveAspectRatio="none"
        role="img"
        aria-label="Five stages connect in sequence: traces, human-reviewed outcomes, isolated tool tests, held-out regression, and canary promotion."
      >
        <title>Agent improvement loop</title>
        <desc>Review observed outcomes, test tools in isolation, check held-out regressions, then promote cautiously with a canary.</desc>
        <line x1="100" y1="36" x2="900" y2="36" class="loop-line" />
        <line
          v-for="index in stages.length - 1"
          :key="`progress-${index}`"
          :x1="100 + (index - 1) * 200"
          :x2="100 + index * 200"
          y1="36"
          y2="36"
          :class="['loop-line-progress', { 'is-complete': index <= activeIndex }]"
        />
        <g
          v-for="(stage, index) in stages"
          :key="stage"
          :class="['loop-marker', { 'is-current': index === activeIndex, 'is-complete': index < activeIndex }]"
        >
          <circle :cx="100 + index * 200" cy="36" r="13" class="loop-marker-halo" />
          <circle :cx="100 + index * 200" cy="36" r="7" class="loop-marker-dot" />
        </g>
      </svg>

      <ol class="loop-stages" aria-label="Improvement stages">
        <li v-for="(stage, index) in stages" :key="stage">
          <button
            type="button"
            class="loop-stage"
            :class="{ 'is-current': index === activeIndex }"
            :aria-pressed="index === activeIndex"
            @click="selectStage(index)"
          >
            <span class="loop-stage-number">0{{ index + 1 }}</span>
            <span>{{ stage }}</span>
          </button>
        </li>
      </ol>
    </div>

    <footer class="loop-footer">
      <div class="loop-controls">
        <button
          type="button"
          class="loop-playback"
          :disabled="reducedMotion"
          :aria-pressed="playing"
          @click="togglePlayback"
        >
          {{ playing ? 'Pause' : 'Play' }} loop
        </button>
        <span class="loop-status" :aria-live="playing ? 'off' : 'polite'">
          {{ reducedMotion ? 'Auto-play off · reduced motion' : `${playing ? 'Playing' : 'Paused'} · ${activeStage}` }}
        </span>
      </div>
      <p class="loop-preview-copy">Learn from reviewed outcomes before changing the agent.</p>
    </footer>
  </section>
</template>
