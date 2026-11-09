<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, decisionsBlocker, type DemoStatus } from '../demo-api'

const message = ref('Checking the connection…')
const checking = ref(true)

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
  finally {
    checking.value = false
  }
}
onMounted(checkStatus)
</script>

<template>
  <section v-if="message" class="demo run-mode" aria-label="Code runner" @keydown.stop @click.stop>
    <div class="demo-toolbar">
      <span class="run-status" :class="{ 'live-signal': checking }" :data-live-state="checking ? 'live' : undefined" role="status">{{ message }}</span>
    </div>
  </section>
</template>
