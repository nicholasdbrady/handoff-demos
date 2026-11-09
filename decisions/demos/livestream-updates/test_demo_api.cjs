const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('typescript')

const source = ts.transpileModule(fs.readFileSync(`${__dirname}/demo-api.ts`, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText

function client(response) {
  const module = { exports: {} }
  new Function('exports', 'fetch', source)(module.exports, async () => response)
  return module.exports
}

for (const status of [502, 503, 504]) {
  test(`Empty proxy ${status} reports local adapter guidance`, async () => {
    await assert.rejects(client(new Response('', { status })).api('status'), /Start demo_server.py on port 8765/)
  })
  test(`Explicit server detail survives ${status}`, async () => {
    await assert.rejects(client(new Response(JSON.stringify({ detail: 'Azure permission denied.' }), { status })).api('status'), /^Error: Azure permission denied\.$/)
  })
  for (const body of ['null', '{"detail":null}', '"unavailable"']) {
    test(`Missing string detail (${body}) on ${status} reports adapter guidance`, async () => {
      await assert.rejects(client(new Response(body, { status })).api('status'), /Start demo_server.py on port 8765/)
    })
  }
}

test('Other HTTP failures retain generic status', async () => {
  await assert.rejects(client(new Response('', { status: 400 })).api('status'), /Demo request failed \(400\)/)
})
