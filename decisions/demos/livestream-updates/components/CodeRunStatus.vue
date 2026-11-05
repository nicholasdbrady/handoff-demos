<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, decisionsBlocker, type DemoStatus } from '../demo-api'

const message = ref('Checking the connection…')

async function checkStatus() {
  try {
    const status = await api<DemoStatus>('status')
    const blocker = !status.code_run_enabled
      ? 'Not connected. Set SLIDEV_ENABLE_CODE_RUN=1 in .env and restart demo_server.py.'
      : decisionsBlocker(status)
    message.value = blocker ?? ''
  }
  catch (cause) {
    message.value = cause instanceof Error ? cause.message : 'Cannot reach the demo server.'
  }
}
onMounted(checkStatus)
</script>

<template>
  <section v-if="message" class="demo run-mode" aria-label="Code runner" @keydown.stop @click.stop>
    <div class="demo-toolbar">
      <span class="run-status" role="status">{{ message }}</span>
    </div>
  </section>
</template>
