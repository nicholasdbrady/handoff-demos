import type { LiveEvent, LiveResult } from './demo-stream'

export interface ChatEntry {
  id: number
  kind: 'assistant' | 'tool' | 'step' | 'error' | 'reasoning'
  text: string
  name?: string
  state?: string
  call?: boolean
  at_ms?: number
}

export function appendEvent(entries: ChatEntry[], event: LiveEvent, receivedAt?: number): void {
  const at_ms = receivedAt ?? event.at_ms
  if (event.type === 'delta') {
    const last = entries.at(-1)
    if (last?.kind === 'assistant') last.text += event.text
    else entries.push({ id: entries.length, kind: 'assistant', text: event.text, at_ms })
  } else if (event.type === 'reasoning') {
    const last = entries.at(-1)
    if (last?.kind === 'reasoning' && last.state !== 'done') {
      last.text += event.text ?? ''
      last.state = event.state
    } else {
      entries.push({ id: entries.length, kind: 'reasoning', text: event.text ?? '', state: event.state, at_ms })
    }
  } else if (event.type === 'tool' || event.type === 'step') {
    const name = event.name ?? event.type
    if (event.type === 'tool' && event.detail === 'completed') {
      const active = [...entries].reverse().find(entry => entry.kind === 'tool' && entry.name === name && entry.state === 'started')
      if (active) { active.state = 'completed'; return }
    }
    entries.push({
      id: entries.length, kind: event.type, name, at_ms,
      text: event.text ?? (event.type === 'step' ? event.detail ?? '' : ''),
      state: event.type === 'tool' ? event.detail : undefined,
      call: event.type === 'tool' && event.detail === 'started' && !name.includes('output'),
    })
  } else if (event.type === 'error') {
    entries.push({ id: entries.length, kind: 'error', text: event.message, at_ms })
  }
}

export function finishTranscript(entries: ChatEntry[], text: string, at_ms?: number): void {
  const last = entries.at(-1)
  if (last?.kind === 'assistant') last.text = text
  else if (text) entries.push({ id: entries.length, kind: 'assistant', text, at_ms })
}

export function recordedTranscript(result: LiveResult): ChatEntry[] {
  const entries: ChatEntry[] = []
  if (result.stream_events?.length) {
    for (const event of result.stream_events) appendEvent(entries, event)
  } else {
    const raw = objectValue(result.raw)
    const output = Array.isArray(raw?.output) ? raw.output : []
    for (const value of output) {
      const item = objectValue(value)
      if (item?.type === 'reasoning' && Array.isArray(item.summary)) {
        const text = item.summary.map(part => objectValue(part)?.text).filter(value => typeof value === 'string').join('\n')
        if (text) entries.push({ id: entries.length, kind: 'reasoning', text, state: 'done' })
      }
      if (item?.type === 'function_call' && typeof item.name === 'string') {
        entries.push({ id: entries.length, kind: 'tool', name: item.name, text: '',
          state: typeof item.status === 'string' ? item.status : undefined, call: true })
      }
    }
    if (!entries.length) {
      for (const name of result.events ?? []) {
        if (name !== 'reasoning' && !name.includes('output')) {
          entries.push({ id: entries.length, kind: 'tool', name, text: '', state: 'completed', call: true })
        }
      }
    }
  }
  finishTranscript(entries, result.text)
  return entries
}

function objectValue(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown> : undefined
}

export function provenanceLabel(result?: LiveResult | null): string {
  const reference = objectValue(objectValue(result?.raw)?.agent_reference)
  const version = result?.provenance?.version ?? reference?.version
  const transport = result?.transport ?? 'managed'
  return `${transport}${typeof version === 'string' || typeof version === 'number' ? ` · v${version}` : ''}`
}

export function toolTitle(name: string): string {
  const titles: Record<string, string> = {
    skill: 'Read review skill', view: 'Read workspace file', glob: 'Find workspace files',
    shell_call: 'Run shell check', shell_call_output: 'Shell output',
    function_call_output: 'Tool output', apply_patch: 'Write workspace files',
    web_fetch: 'Fetch source', task: 'Delegate to reviewer',
    upload_file_from_workspace_to_foundry_project: 'Upload generated file',
    quota_wait: 'Model quota wait', write_artifact: 'Write artifact',
    response_created: 'Response created', primary_started: 'Primary started',
    fusion_started: 'Fusion worker started',
    primary_completed: 'Primary completed', judge_started: 'Judge started',
    judge_completed: 'Judge completed', route_selected: 'Route selected',
    read_artifact: 'Read artifact', inspect_workspace: 'Validate workspace',
  }
  return titles[name] ?? name.replaceAll('_', ' ')
}

export function toolIcon(name: string): string {
  if (/shell|validate|inspect/.test(name)) return 'm5 7 4 5-4 5m7 0h7M3 3h18v18H3z'
  if (/web|source/.test(name)) return 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M3 12h18M12 3c-5 5-5 13 0 18 5-5 5-13 0-18'
  if (/task|review|delegate/.test(name)) return 'M9 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6M3 21v-3a6 6 0 0 1 12 0v3m2-16a3 3 0 0 1 0 6m2 3a6 6 0 0 1 2 4v3'
  if (/quota|wait/.test(name)) return 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18m0 4v5l3 2'
  return 'M6 3h8l4 4v14H6zm8 0v5h5M9 12h6m-6 4h6'
}

export interface InlinePart { kind: 'text' | 'code' | 'strong'; text: string }
export interface MarkdownBlock { kind: 'paragraph' | 'heading' | 'list' | 'code'; text: string; items?: string[] }

export function presentationText(text: string): string {
  return text.replace(/\b(?:assistant-|caresp_|conv_|call_)[A-Za-z0-9_-]+/g, '[identifier hidden]')
    .replace(/\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b/gi, '[identifier hidden]')
}

export function presentationJson(value: unknown): unknown {
  if (typeof value === 'string') return presentationText(value)
  if (Array.isArray(value)) return value.map(presentationJson)
  const record = objectValue(value)
  return record ? Object.fromEntries(Object.entries(record).filter(([key]) =>
    key !== 'encrypted_content' && !(record.type === 'reasoning' && key === 'content')).map(([key, item]) =>
    [key, /^(?:id|.*_id|tenantId|subscriptionId|principalId)$/.test(key) ? '[identifier hidden]' : presentationJson(item)])) : value
}

export function inlineParts(text: string): InlinePart[] {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean).map(part =>
    part.startsWith('`') && part.endsWith('`') ? { kind: 'code', text: part.slice(1, -1) }
      : part.startsWith('**') && part.endsWith('**') ? { kind: 'strong', text: part.slice(2, -2) }
        : { kind: 'text', text: part })
}

export function markdownBlocks(text: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = []
  const lines = text.replaceAll('\r', '').split('\n')
  let index = 0
  while (index < lines.length) {
    const line = lines[index++]
    if (!line.trim()) continue
    if (/^\s*```/.test(line)) {
      const code: string[] = []
      while (index < lines.length && !/^\s*```/.test(lines[index])) code.push(lines[index++])
      if (index < lines.length) index++
      blocks.push({ kind: 'code', text: code.join('\n') })
    } else if (/^#{1,6}\s/.test(line)) {
      blocks.push({ kind: 'heading', text: line.replace(/^#{1,6}\s+/, '') })
    } else if (/^\s*(?:[-*]|\d+\.)\s/.test(line)) {
      const items = [line.replace(/^\s*(?:[-*]|\d+\.)\s+/, '')]
      while (index < lines.length && /^\s*(?:[-*]|\d+\.)\s/.test(lines[index])) {
        items.push(lines[index++].replace(/^\s*(?:[-*]|\d+\.)\s+/, ''))
      }
      blocks.push({ kind: 'list', text: '', items })
    } else {
      const paragraph = [line]
      while (index < lines.length && lines[index].trim() && !/^\s*(?:```|#{1,6}\s|[-*]\s|\d+\.\s)/.test(lines[index])) {
        paragraph.push(lines[index++])
      }
      blocks.push({ kind: 'paragraph', text: paragraph.join('\n') })
    }
  }
  return blocks
}
