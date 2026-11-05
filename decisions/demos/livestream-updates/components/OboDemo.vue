<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type DemoStatus, type OboResult } from '../demo-api'

const ready = ref(false)
const busy = ref(false)
const revealed = ref(false)
const result = ref<OboResult>()
const error = ref('')
const phase = ref('')
const setupMessage = ref('Checking the connection…')

async function checkStatus() {
  ready.value = false
  try {
    const status = await api<DemoStatus>('status')
    ready.value = status.live_enabled && status.obo_configured
    setupMessage.value = !status.live_enabled
      ? 'Not connected. Set SLIDEV_ENABLE_LIVE=1 in .env and restart demo_server.py.'
      : `Not connected. Missing: ${status.obo_missing_settings.join(', ')}.`
    error.value = ''
  }
  catch (cause) {
    setupMessage.value = cause instanceof Error ? cause.message : 'Cannot reach the demo server.'
  }
}

async function call(action: 'start' | 'continue' | 'reset') {
  if (busy.value) return
  busy.value = true
  revealed.value = false
  error.value = ''
  phase.value = action === 'start' ? 'Finish Microsoft sign-in in the separate browser window.' : 'Waiting for the agent response…'
  try {
    if (action === 'reset') {
      await api('obo/reset', {})
      result.value = undefined
    }
    else result.value = await api<OboResult>(`obo/${action}`, action === 'start' ? { mode: 'live', audience: 'blueprint' } : {})
  }
  catch (cause) { error.value = cause instanceof Error ? cause.message : 'The agent request failed.' }
  finally { busy.value = false }
}
onMounted(checkStatus)
</script>

<template>
  <section class="demo obo-demo" aria-label="Interactive Agent OBO demo" @keydown.stop @click.stop>
    <div v-if="!ready" class="demo-toolbar">
      <span class="run-status" role="status">{{ setupMessage }}</span>
    </div>
    <div class="obo-workspace">
      <div class="obo-controls">
        <p class="query">“Read my profile at /me with Work IQ.”</p>
        <p class="micro">Sign-in and consent open in Microsoft's browser flow.</p>
        <div class="button-row">
          <button class="primary" :disabled="busy || !ready || !!result" @click="call('start')">Sign in &amp; call agent</button>
          <button :disabled="busy" @click="call('reset')">Reset session</button>
        </div>
      </div>
      <div class="obo-output" aria-live="polite" :aria-busy="busy">
        <p v-if="busy" class="waiting">{{ phase }}</p>
        <div v-else-if="!result" class="empty-state">
          <strong>User + agent. Not a shared key.</strong>
          <p>Sign in, then the agent calls the tool on your behalf.</p>
        </div>
        <template v-else>
          <div class="result-heading"><strong>{{ result.status.replaceAll('_', ' ') }}</strong></div>
          <p class="result-message">{{ result.message }}</p>
          <div v-if="result.status === 'consent_required'" class="consent-actions">
            <a v-for="(item, index) in result.consent.filter(item => item.url)" :key="index" :href="item.url!" target="_blank" rel="noopener noreferrer" class="consent-link">Open Microsoft consent for {{ item.label }}</a>
            <button class="primary" :disabled="busy" @click="call('continue')">I finished consent · continue</button>
          </div>
          <div v-for="(tool, index) in result.tools" :key="index" class="tool-row"><code>{{ tool.name }}</code><span>{{ tool.status }}</span></div>
          <template v-if="result.text">
            <button v-if="!revealed" class="reveal" @click="revealed = true">Reveal response</button>
            <p v-else class="agent-response">{{ result.text }}</p>
          </template>
        </template>
      </div>
    </div>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
  </section>
</template>
