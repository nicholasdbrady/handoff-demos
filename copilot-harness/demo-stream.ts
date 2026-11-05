export interface LiveResult {
  mode?: string
  text: string
  elapsed_ms: number
  usage: { input_tokens?: number; output_tokens?: number; total_tokens?: number; output_tokens_details?: { reasoning_tokens?: number } }
  first_text_ms?: number | null
  cost_usd: number | null
  events?: string[]
  raw: unknown
  files?: { id?: string; name?: string; path?: string; content?: string }[]
  transport?: string
  usage_note?: string
  quota_retries?: number
  artifact_export?: { note: string }
  provenance?: { agent?: string; version?: string | number; model?: string; region?: string; transport?: string }
  stream_events?: LiveEvent[]
}

export type LiveEvent = (
  | { type: 'start'; lane?: string }
  | { type: 'delta'; text: string }
  | { type: 'tool' | 'step'; name?: string; detail?: string; text?: string }
  | { type: 'result'; result: LiveResult }
  | { type: 'error'; message: string }
  | { type: 'reasoning'; state: 'start' | 'delta' | 'done'; text?: string }
) & { at_ms?: number }

export async function streamDemo(path: string, receive: (event: LiveEvent) => void, signal?: AbortSignal): Promise<LiveResult> {
  const response = await fetch(`/demo-api/stream/${path}`, {
    method: 'POST', headers: { 'X-Demo-Client': 'slidev' },
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(590_000)]) : AbortSignal.timeout(590_000),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail ?? `Live request failed (${response.status}).`)
  }
  if (!response.body) throw new Error('The server did not return a readable stream.')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let result: LiveResult | undefined
  function consume(line: string) {
    if (!line.trim()) return
    const event = JSON.parse(line) as LiveEvent
    receive(event)
    if (event.type === 'error') throw new Error(event.message)
    if (event.type === 'result') result = event.result
  }
  try {
    while (true) {
      const { done, value } = await reader.read()
      pending += decoder.decode(value, { stream: !done })
      const lines = pending.split('\n')
      pending = lines.pop() ?? ''
      for (const line of lines) consume(line)
      if (done) break
    }
    consume(pending)
  } finally { reader.releaseLock() }
  if (!result) throw new Error('The stream ended without a completed result.')
  return result
}
