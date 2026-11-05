<script setup lang="ts">
import { computed } from 'vue'
import { inlineParts, markdownBlocks, presentationText } from '../chat-transcript'
const props = defineProps<{ text: string }>()
const blocks = computed(() => markdownBlocks(presentationText(props.text)))
</script>

<template>
  <div class="chat-markdown">
    <template v-for="(block, index) in blocks" :key="index">
      <pre v-if="block.kind === 'code'"><code>{{ block.text }}</code></pre>
      <ul v-else-if="block.kind === 'list'">
        <li v-for="(item, itemIndex) in block.items" :key="itemIndex"><template v-for="(part, partIndex) in inlineParts(item)" :key="partIndex"><code v-if="part.kind === 'code'">{{ part.text }}</code><strong v-else-if="part.kind === 'strong'">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></li>
      </ul>
      <component :is="block.kind === 'heading' ? 'h4' : 'p'" v-else><template v-for="(part, partIndex) in inlineParts(block.text)" :key="partIndex"><code v-if="part.kind === 'code'">{{ part.text }}</code><strong v-else-if="part.kind === 'strong'">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></component>
    </template>
  </div>
</template>
