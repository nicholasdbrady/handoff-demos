import type { CodeRunnerOutputs } from '@slidev/types'
import { api, type Mode } from './demo-api'

export interface CodeRunResult {
  mode: Mode
  model: string
  stdout: string
  stderr: string
  exit_code: number | null
  timed_out: boolean
}

const escape = (text: string) => text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export async function runPython(code: string): Promise<CodeRunnerOutputs> {
  try {
    const result = await api<CodeRunResult>('run', { mode: 'live', code })
    // The adapter only answers in rehearsal when a test rewrites the request.
    const parts: string[] = result.mode === 'rehearsal'
      ? ['<p class="run-badge">REHEARSAL · test client</p>']
      : []
    if (result.stdout)
      parts.push(`<pre class="py-out">${escape(result.stdout)}</pre>`)
    if (result.stderr)
      parts.push(`<pre class="py-err">${escape(result.stderr)}</pre>`)
    if (!result.stdout && !result.stderr)
      parts.push('<p class="py-note">No output. Add print(...) to show a result.</p>')
    return { html: parts.join('') }
  }
  catch (cause) {
    return { error: cause instanceof Error ? cause.message : 'The code run failed.' }
  }
}
