const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const Module = require('node:module')
const ts = require('typescript')
const source = path.join(__dirname, 'chat-transcript.ts')
const compiled = ts.transpileModule(fs.readFileSync(source, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText
const loaded = new Module(source, module)
loaded.filename = source
loaded._compile(compiled, source)
const { appendEvent, finishTranscript, recordedTranscript, markdownBlocks, inlineParts, provenanceLabel, presentationText, presentationJson } = loaded.exports

test('real deltas and tool lifecycles retain transcript order without invented times', () => {
  const entries = []
  appendEvent(entries, { type: 'delta', text: 'Checking ' })
  appendEvent(entries, { type: 'delta', text: 'the notebook.' })
  appendEvent(entries, { type: 'tool', name: 'shell_call', detail: 'started' })
  appendEvent(entries, { type: 'tool', name: 'shell_call', detail: 'completed' })
  appendEvent(entries, { type: 'tool', name: 'shell_call_output', detail: 'started' })
  appendEvent(entries, { type: 'delta', text: 'Syntax passed.' })
  assert.deepEqual(entries.map(row => row.kind), ['assistant', 'tool', 'tool', 'assistant'])
  assert.equal(entries[0].text, 'Checking the notebook.')
  assert.equal(entries[1].state, 'completed')
  assert.equal(entries.filter(row => row.call).length, 1)
  assert.ok(entries.every(row => !('duration' in row)))
})

test('quota waits and real errors remain visible, not a replay', () => {
  const entries = []
  appendEvent(entries, { type: 'step', name: 'quota_wait', detail: 'Wait 65 seconds.' })
  appendEvent(entries, { type: 'error', message: 'Actual service failure.' })
  assert.equal(entries[0].text, 'Wait 65 seconds.')
  assert.equal(entries[1].kind, 'error')
  assert.equal(entries[1].text, 'Actual service failure.')
})

test('synthetic baseline and managed fixtures do not invent tools or artifacts', () => {
  const baseline = JSON.parse(fs.readFileSync(path.join(__dirname, 'public/recordings/default.json')))
  const managed = JSON.parse(fs.readFileSync(path.join(__dirname, 'public/recordings/copilot.json')))
  assert.equal(recordedTranscript(baseline).filter(row => row.call).length, 0)
  assert.equal(recordedTranscript(managed).filter(row => row.call).length, 0)
  assert.equal(managed.files.length, 0)
  assert.equal(managed.mode, 'synthetic')
})

test('synthetic hosted fixture retains honest provenance without invented calls', () => {
  const result = JSON.parse(fs.readFileSync(path.join(__dirname, 'public/recordings/hosted-sdk.json')))
  const entries = recordedTranscript(result)
  assert.equal(entries.filter(row => row.call).length, 0)
  assert.equal(entries.at(-1).kind, 'assistant')
  assert.match(provenanceLabel(result), /synthetic/)
})

test('markdown remains escaped Vue text and supports the required light syntax', () => {
  const blocks = markdownBlocks('# Heading\n\nA **bold** `value`.\n\n- One\n- Two\n\n```python\nprint("<script>")\n```')
  assert.deepEqual(blocks.map(row => row.kind), ['heading', 'paragraph', 'list', 'code'])
  assert.deepEqual(inlineParts('A **bold** `value`.').map(row => row.kind), ['text', 'strong', 'text', 'code', 'text'])
  assert.equal(blocks.at(-1).text, 'print("<script>")')
  assert.doesNotMatch(fs.readFileSync(path.join(__dirname, 'components/ChatMessage.vue'), 'utf8'), /v-html/)
})

test('final response replaces only the final streamed assistant message', () => {
  const entries = []
  appendEvent(entries, { type: 'tool', name: 'skill', detail: 'started' })
  appendEvent(entries, { type: 'delta', text: 'partial' })
  finishTranscript(entries, 'Actual final text.')
  assert.equal(entries.length, 2)
  assert.equal(entries[1].text, 'Actual final text.')
})

test('presentation redacts opaque identifiers without changing saved evidence', () => {
  const raw = { id: 'opaque', usage: { input_tokens: 123 }, text: 'Uploaded assistant-TestFile' }
  assert.equal(presentationText(raw.text), 'Uploaded [identifier hidden]')
  assert.deepEqual(presentationJson(raw), { id: '[identifier hidden]', usage: { input_tokens: 123 }, text: 'Uploaded [identifier hidden]' })
  assert.equal(raw.id, 'opaque')
})

test('only actual supported summaries appear in reasoning entries with measured times', () => {
  const entries = []
  appendEvent(entries, { type: 'reasoning', state: 'start', at_ms: 100 })
  appendEvent(entries, { type: 'reasoning', state: 'delta', text: 'Checking ', at_ms: 200 })
  appendEvent(entries, { type: 'reasoning', state: 'delta', text: 'the constraints.', at_ms: 300 })
  appendEvent(entries, { type: 'reasoning', state: 'done', at_ms: 400 })
  appendEvent(entries, { type: 'delta', text: 'Answer.', at_ms: 500 })
  assert.equal(entries[0].text, 'Checking the constraints.')
  assert.equal(entries[0].state, 'done')
  assert.equal(entries[0].at_ms, 100)
  assert.equal(entries[1].at_ms, 500)
  assert.equal(entries.filter(row => row.call).length, 0)
  assert.deepEqual(presentationJson({ type: 'reasoning', encrypted_content: 'secret', content: 'private', summary: [{ text: 'Supported summary' }] }),
    { type: 'reasoning', summary: [{ text: 'Supported summary' }] })
})
