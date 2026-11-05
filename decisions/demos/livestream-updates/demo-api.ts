export type Mode = 'rehearsal' | 'live'
export type Answer =
  | { type: 'predicate'; name: string; probability: number }
  | { type: 'choice'; name: string; choice: string; confidence: number; probabilities: { value: string; probability: number }[] }
  | { type: 'score'; name: string; score: number; confidence: number; probabilities: { value: number; label: string; probability: number }[] }
  | { type: 'refusal'; name: string | null }

export interface DecisionResult {
  mode: Mode
  answers: Answer[]
  model: string
  elapsed_ms: number | null
  usage: { input_tokens: number; output_tokens: number }
}

export interface System1Result {
  mode: Mode
  model: string
  answers: Answer[]
  usage: { input_tokens: number; output_tokens: number }
  cost_usd: number | null
  raw: unknown
  elapsed_ms: number | null
}

export interface System2Result {
  mode: Mode
  model: string
  effort: string
  summary: string[]
  text: string
  usage: { input_tokens: number; output_tokens: number; reasoning_tokens: number }
  cost_usd: number | null
  raw: unknown
  elapsed_ms: number | null
}

/** The Python SDK call each lane sends for one ticket. */
export interface SystemCode { system1: string; system2: string }

export interface DemoStatus {
  live_enabled: boolean
  code_run_enabled: boolean
  decisions_configured: boolean
  systemone_configured: boolean
  obo_configured: boolean
  obo_missing_settings: string[]
}

export interface NativeResult {
  mode: Mode
  elapsed_ms: number | null
  cost_usd?: number | null
  cost_note?: string
  raw: unknown
}

export interface ImageResult extends NativeResult {
  raw: Pick<DecisionResult, 'model' | 'answers' | 'usage'>
  route: { label: 'ready' | 'repack' | 'review'; reason: string } | null
}

/** Return null when Azure OpenAI calls can run, or the setup step that is missing. */
export function decisionsBlocker(status: DemoStatus): string | null {
  if (!status.live_enabled) return 'Not connected. Set SLIDEV_ENABLE_LIVE=1 in .env and restart demo_server.py.'
  if (!status.decisions_configured) return 'Not connected. Set AZURE_OPENAI_ENDPOINT in .env and restart demo_server.py.'
  return null
}

export interface OboResult {
  mode: Mode
  status: 'consent_required' | 'completed' | 'failed'
  text: string
  tools: { name: string; status: string }[]
  consent: { label: string; url: string | null }[]
  message: string
}

export async function api<T>(path: string, body?: object): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/demo-api/${path}`, {
      method: body ? 'POST' : 'GET',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-Demo-Client': 'slidev' },
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(350_000),
    })
  }
  catch {
    throw new Error('The local demo server did not respond. Start demo_server.py on port 8765, then retry. A timed-out request can still be running; wait before you repeat a live sign-in.')
  }
  if (!response.ok) {
    const error: { detail?: unknown } = await response.json().catch(() => ({}))
    throw new Error(typeof error.detail === 'string' ? error.detail : `Demo request failed (${response.status}). Check the local server and configuration.`)
  }
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('The demo API is unavailable on this host. Use npm run dev with demo_server.py; a static deck does not include the backend.')
  }
  return response.json() as Promise<T>
}
