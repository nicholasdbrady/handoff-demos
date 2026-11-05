<script setup lang="ts">
import { computed } from 'vue'
import { tokens } from '../code-tokens'

const props = defineProps<{ source: string; label: string }>()
const parts = computed(() => tokens(props.source))
</script>

<template>
  <pre class="lane-code" tabindex="0" :aria-label="label"><span v-for="(part, index) in parts" :key="index" :class="part.kind">{{ part.text }}</span></pre>
</template>
