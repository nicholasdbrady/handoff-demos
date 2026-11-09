<script setup lang="ts">
import { ref } from 'vue'

const verified = ref(false)

function toggleVerification() {
  verified.value = !verified.value
}
</script>

<template>
  <section class="verified-state" aria-labelledby="verified-state-title">
    <header class="verified-header">
      <div>
        <h2 id="verified-state-title">Verify the final state</h2>
        <p class="verified-illustrative">ILLUSTRATIVE · synthetic missing-file example</p>
      </div>
      <button
        type="button"
        class="verified-action"
        :aria-pressed="verified"
        @click="toggleVerification"
      >
        {{ verified ? 'Reset check' : 'Check final state' }}
      </button>
    </header>

    <div class="verified-content">
      <div class="verified-comparison" aria-label="Claimed result compared with verified final state">
        <section class="verified-column">
          <h3>Says done</h3>
          <p class="verified-claim">“report.csv saved”</p>
          <p class="verified-detail">Tool-reported success</p>
        </section>
        <section class="verified-column verified-observation">
          <h3>Verified final state</h3>
          <p class="verified-result" :data-verified="verified">
            {{ verified ? 'report.csv is missing' : 'Not checked yet' }}
          </p>
          <p class="verified-detail">
            {{ verified ? 'Observed after the action' : 'Run a check to inspect the result' }}
          </p>
        </section>
      </div>

      <figure class="verified-chart">
        <figcaption>
          <span class="verified-chart-title">Research snapshot</span>
          <span class="verified-chart-summary">38 → 107 of 507 · all 20 attempts passed</span>
        </figcaption>
        <svg
          viewBox="0 0 520 132"
          role="img"
          aria-label="Illustrative research chart: verified outcomes increased from 38 to 107 out of 507. All 20 attempts passed."
        >
          <title>Verified outcomes: 38 to 107 out of 507</title>
          <desc>Two bars compare 38 and 107 verified outcomes on a scale of 507. The result passed all 20 attempts.</desc>
          <text x="0" y="37" class="verified-bar-label">Before</text>
          <rect x="94" y="16" width="370" height="28" rx="4" class="verified-bar-track" />
          <rect x="94" y="16" width="28" height="28" rx="4" class="verified-bar" />
          <text x="132" y="37" class="verified-bar-value">38</text>
          <text x="0" y="91" class="verified-bar-label">After</text>
          <rect x="94" y="70" width="370" height="28" rx="4" class="verified-bar-track" />
          <rect x="94" y="70" width="78" height="28" rx="4" class="verified-bar verified-bar-strong" />
          <text x="182" y="91" class="verified-bar-value">107</text>
          <text x="94" y="124" class="verified-axis-label">0</text>
          <text x="464" y="124" text-anchor="end" class="verified-axis-label">507 outcomes</text>
        </svg>
        <p class="verified-chart-note">Research-trained Qwen checkpoint</p>
      </figure>
    </div>
    <p class="verified-live-status" role="status" aria-live="polite">
      {{ verified ? 'Check complete: the claimed file was not found.' : 'No final-state check has run.' }}
    </p>
  </section>
</template>
