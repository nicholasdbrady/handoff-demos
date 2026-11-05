<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, decisionsBlocker, type DemoStatus, type ImageResult } from '../demo-api'
import RunMetrics from './RunMetrics.vue'

const withBrief = ref(false)
const briefs = {
  beach: 'A sunny beach weekend. Choose light clothing, sun protection, and beach footwear.',
  rain: 'Plot twist: a cold, rainy outdoor festival with muddy paths. Choose rain protection, covering clothing, and closed footwear.',
}
const fixture = ref<'sunshine' | 'rain' | 'obscured'>('sunshine')
const scenes = [
  { value: 'sunshine', label: 'Sunshine kit' },
  { value: 'rain', label: 'Rain kit' },
  { value: 'obscured', label: 'Under cover' },
] as const
const sceneIndex = computed(() => scenes.findIndex(scene => scene.value === fixture.value))
function moveScene(direction: number) {
  if (!busy.value) fixture.value = scenes[(sceneIndex.value + direction + scenes.length) % scenes.length].value
}
const brief = ref(briefs.beach)
const ready = ref(false)
const status = ref('')
const code = ref('')
type ImageQuestion = { name: string; type: string; instructions: string }
const questions = ref<ImageQuestion[]>([])
const selectedQuestion = ref('rain_protection')
const instructions = ref<Record<string, string>>({})
const selectedInstructions = computed({
  get: () => instructions.value[selectedQuestion.value] ?? questions.value.find(q => q.name === selectedQuestion.value)?.instructions ?? '',
  set: (value: string) => { instructions.value = { ...instructions.value, [selectedQuestion.value]: value } },
})
const validInstructions = computed(() => Object.values(instructions.value).every(value => value.trim().length > 0))
const busy = ref(false)
const error = ref('')
const view = ref<'answers' | 'code' | 'json'>('answers')
const result = ref<ImageResult>()
const displayAnswers = computed(() => {
  const answers = result.value?.raw.answers ?? []
  return [...answers.filter(a => a.name === 'trip_fit'), ...answers.filter(a => a.name !== 'trip_fit')]
})
let revision = 0
const body = () => ({
  fixture: fixture.value, context: withBrief.value ? 'brief' : 'visual', brief: brief.value,
  ...(!withBrief.value ? { instructions: instructions.value } : {}),
})
const labels: Record<string, string> = {
  rain_protection: 'Rain protection visible?', footwear: 'Visible footwear',
  evidence_quality: 'Can we inspect the contents?', trip_fit: 'Fit for this trip',
  open: 'Open sandals', closed: 'Closed shoes / boots', unclear: 'Unclear',
  clear: 'Clear view', obscured: 'Obscured',
}
const routeLabels = { ready: 'Ready for this brief', repack: 'Repack', review: 'Need a closer look' }

async function loadCode() {
  const current = ++revision
  result.value = undefined
  code.value = ''
  error.value = ''
  try {
    const response = await api<{ code: string; questions: ImageQuestion[] }>('image-code', body())
    if (current === revision) {
      code.value = response.code
      questions.value = response.questions
    }
  }
  catch (cause) {
    if (current === revision) error.value = cause instanceof Error ? cause.message : 'Cannot load the image example.'
  }
}

async function run() {
  if (busy.value) return
  const current = revision
  busy.value = true
  result.value = undefined
  error.value = ''
  try {
    const response = await api<ImageResult>('image-decisions', { ...body(), mode: 'live' })
    if (current === revision) result.value = response
  }
  catch (cause) {
    if (current === revision) error.value = cause instanceof Error ? cause.message : 'Image evaluation failed.'
  }
  finally { busy.value = false }
}

watch([fixture, brief, instructions, withBrief], loadCode, { flush: 'sync' })
onMounted(async () => {
  await loadCode()
  try {
    status.value = decisionsBlocker(await api<DemoStatus>('status')) ?? ''
    ready.value = !status.value
  }
  catch (cause) { status.value = cause instanceof Error ? cause.message : 'Cannot reach the adapter.' }
})
</script>

<template>
  <section class="demo image-demo" :class="{ 'image-demo-visual': !withBrief }" :aria-label="withBrief ? 'Pack for the Plot Twist' : 'Suitcase image decisions'" @keydown.stop @click.stop>
    <div v-if="status" class="demo-toolbar"><span class="run-status" role="status">{{ status }}</span></div>
    <div class="view-switch suitcase-mode" role="group" aria-label="Suitcase demo mode">
      <button :disabled="busy" :aria-pressed="!withBrief" @click="withBrief = false">Inspect the image</button>
      <button :disabled="busy" :aria-pressed="withBrief" @click="withBrief = true">Add a trip brief</button>
    </div>
    <div class="image-workspace">
      <div class="image-evidence">
        <div class="scene-carousel" role="group" aria-label="Suitcase scenarios">
          <button :disabled="busy" aria-label="Previous suitcase" @click="moveScene(-1)">←</button>
          <div aria-live="polite"><strong>{{ scenes[sceneIndex].label }}</strong><small>{{ sceneIndex + 1 }} of {{ scenes.length }}</small></div>
          <button :disabled="busy" aria-label="Next suitcase" @click="moveScene(1)">→</button>
        </div>
        <img :src="`/packing/${fixture}.png`" :alt="fixture === 'obscured' ? 'Synthetic suitcase photograph with equipment hidden under opaque covers' : fixture === 'rain' ? 'Synthetic suitcase photograph with a hooded coat, umbrella, and rubber boots' : 'Synthetic suitcase photograph with light clothing, a straw hat, sunscreen, and flip-flops'">
        <template v-if="withBrief">
          <div class="brief-presets" role="group" aria-label="Trip presets">
            <button :disabled="busy" :aria-pressed="brief === briefs.beach" @click="brief = briefs.beach">Beach weekend</button>
            <button :disabled="busy" :aria-pressed="brief === briefs.rain" @click="brief = briefs.rain">Plot twist: rain</button>
          </div>
          <textarea v-model="brief" aria-label="Trip brief" maxlength="800" :disabled="busy" />
        </template>
        <template v-else>
          <label class="instruction-selector">Model instructions
            <select v-model="selectedQuestion" aria-label="Inspection question" :disabled="busy">
              <option value="rain_protection">Rain protection</option>
              <option value="footwear">Footwear</option>
              <option value="evidence_quality">Evidence quality</option>
            </select>
          </label>
          <textarea v-model="selectedInstructions" aria-label="Inspection instructions" maxlength="800" :disabled="busy || !questions.length" />
        </template>
        <button class="primary" :disabled="busy || !ready || (withBrief ? !brief.trim() : !validInstructions)" @click="run">{{ busy ? 'Evaluating…' : withBrief ? 'Decide for this trip' : 'Inspect the suitcase' }}</button>
      </div>
      <div class="image-output" aria-live="polite" :aria-busy="busy">
        <div class="image-output-toolbar">
        <div class="view-switch" role="group" aria-label="Image decision view">
          <button :aria-pressed="view === 'answers'" @click="view = 'answers'">Answers</button>
          <button :aria-pressed="view === 'code'" @click="view = 'code'">Python</button>
          <button :aria-pressed="view === 'json'" @click="view = 'json'">JSON</button>
        </div>
        <RunMetrics :busy="busy" :result="result" />
        </div>
        <pre v-if="view === 'code'" class="native-code" aria-label="Image request code">{{ code || 'Loading request code…' }}</pre>
        <pre v-else-if="view === 'json' && result" class="native-code" aria-label="Image response JSON">{{ JSON.stringify(result.raw, null, 2) }}</pre>
        <template v-else-if="result && view === 'answers'">
          <p v-if="result.mode === 'rehearsal'" class="micro">REHEARSAL · synthetic answers; no image inference</p>
          <div v-if="result.route" class="packing-route" :data-route="result.route.label">
            <small>APPLICATION RULE · NOT A MODEL ACTION</small>
            <strong>{{ routeLabels[result.route.label] }}</strong>
            <span>{{ result.route.reason }}</span>
          </div>
          <div v-for="answer in displayAnswers" :key="answer.name ?? 'refusal'" class="image-answer">
            <div class="answer-heading"><span>{{ labels[answer.name ?? ''] ?? answer.name ?? 'Question' }}</span>
              <strong v-if="answer.type === 'predicate'">{{ (answer.probability * 100).toFixed(0) }}% p(true)</strong>
              <strong v-else-if="answer.type === 'choice'">{{ labels[answer.choice] ?? answer.choice }}</strong>
              <strong v-else-if="answer.type === 'score'">{{ answer.score.toFixed(2) }} / 2</strong>
              <strong v-else>Refused · review</strong>
            </div>
            <meter v-if="answer.type === 'predicate'" min="0" max="1" :value="answer.probability" :aria-label="labels[answer.name]" />
            <div v-else-if="answer.type === 'choice' || answer.type === 'score'" class="answer-distribution">
              <div v-for="option in answer.probabilities" :key="option.value">
                <span>{{ 'label' in option ? option.label : labels[String(option.value)] ?? option.value }}</span>
                <meter min="0" max="1" :value="option.probability" :aria-label="String(option.value)" />
                <span>{{ (option.probability * 100).toFixed(0) }}%</span>
              </div>
              <small>Confidence {{ answer.confidence.toFixed(2) }} · not an accuracy guarantee</small>
            </div>
          </div>
          <p class="micro">{{ result.raw.usage.input_tokens }} input tokens · {{ result.raw.usage.output_tokens }} output tokens<span v-if="result.elapsed_ms !== null"> · {{ result.elapsed_ms }} ms</span></p>
        </template>
        <div v-else class="packing-empty">
          <strong>{{ busy ? 'Waiting for typed answers…' : withBrief ? 'Same suitcase. Different mission.' : 'Instructions sent to the model' }}</strong>
          <p>{{ withBrief ? 'Vote: ready, repack, or closer look? Change the brief, then run. No call happens until you click.' : 'One image. Three typed decisions. Each question has its own instructions:' }}</p>
          <dl v-if="!withBrief" class="packing-objective">
            <div v-for="question in questions" :key="question.name">
              <dt>{{ labels[question.name] }} <span>{{ question.type === 'predicate' ? 'PREDICATE' : 'CHOICE' }}</span></dt>
              <dd>{{ question.instructions }}</dd>
            </div>
          </dl>
          <small v-if="withBrief">Code applies thresholds; no automatic action. Photos do not prove waterproofing or travel safety.</small>
        </div>
        <p v-if="error" role="alert" class="error">{{ error }}</p>
      </div>
    </div>
  </section>
</template>
