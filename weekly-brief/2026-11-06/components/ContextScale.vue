<script setup lang="ts">
import { computed, ref } from 'vue'

const references = [
  { id: '32k', label: '32K', value: 32_000, x: 69 },
  { id: '128k', label: '128K', value: 128_000, x: 158 },
  { id: '1m', label: '~1M', value: 1_000_000, x: 960 },
] as const

const selectedId = ref<(typeof references)[number]['id']>('1m')
const selectedReference = computed(() => references.find(reference => reference.id === selectedId.value)!)
</script>

<template>
  <section class="context-scale" aria-labelledby="context-scale-title">
    <header class="context-scale-header">
      <div>
        <h2 id="context-scale-title">Context at scale</h2>
      </div>
      <div class="context-inputs" aria-label="Example input types">
        <span>Text input</span>
        <span>Image input</span>
      </div>
    </header>

    <svg
      class="context-scale-graphic"
      viewBox="0 0 1000 170"
      role="img"
      aria-label="Illustrative linear reference scale from zero to about one million context tokens, with markers at 32 thousand, 128 thousand, and about one million."
    >
      <title>Illustrative context scale</title>
      <desc>Linear scale: 32K is near the start, 128K is farther along, and about 1M reaches the end.</desc>
      <line x1="40" y1="58" x2="960" y2="58" class="context-scale-track" />
      <line
        x1="40"
        y1="58"
        :x2="selectedReference.x"
        y2="58"
        class="context-scale-fill"
      />
      <g
        v-for="reference in references"
        :key="reference.id"
        :class="['context-scale-marker', { 'is-selected': selectedId === reference.id }]"
      >
        <line :x1="reference.x" y1="40" :x2="reference.x" y2="78" class="context-scale-tick" />
        <circle :cx="reference.x" cy="58" r="9" class="context-scale-dot" />
        <text
          :x="reference.x"
          y="122"
          :text-anchor="reference.id === '1m' ? 'end' : 'middle'"
          class="context-scale-value"
        >
          {{ reference.label }}
        </text>
        <text
          :x="reference.x"
          y="148"
          :text-anchor="reference.id === '1m' ? 'end' : 'middle'"
          class="context-scale-caption"
        >
          tokens
        </text>
      </g>
      <text x="40" y="28" class="context-scale-endpoint">0</text>
      <text x="960" y="28" text-anchor="end" class="context-scale-endpoint">about 1,000,000</text>
    </svg>

    <div class="context-scale-controls" role="group" aria-label="Select a reference scale">
      <button
        v-for="reference in references"
        :key="reference.id"
        type="button"
        :aria-pressed="selectedId === reference.id"
        :class="{ 'is-selected': selectedId === reference.id }"
        @click="selectedId = reference.id"
      >
        {{ reference.label }}
      </button>
      <span class="context-scale-selection">Selected reference: {{ selectedReference.label }}</span>
    </div>
    <p class="context-scale-note">Illustrative reference scales, not a model specification.</p>
  </section>
</template>
