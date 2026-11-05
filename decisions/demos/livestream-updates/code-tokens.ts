export interface Token { text: string; kind: string }

const TOKEN = /(?<key>"(?:[^"\\\n]|\\.)*"(?=\s*:))|(?<str>"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|(?<com>#[^\n]*|\/\/[^\n]*)|(?<lit>\b(?:true|false|null|True|False|None)\b)|(?<num>-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)|(?<kw>\b(?:from|import|with|as|await|const|let|new|return|async|def|if|else)\b)|(?<arg>\b[a-z_]\w*(?=\s*[=:]))/g

/** Split Python, TypeScript, or JSON into text runs; Vue escapes every run. */
export function tokens(source: string): Token[] {
  const out: Token[] = []
  let last = 0
  for (const match of source.matchAll(TOKEN)) {
    const index = match.index ?? 0
    if (index > last) out.push({ text: source.slice(last, index), kind: '' })
    const kind = Object.entries(match.groups ?? {}).find(([, value]) => value !== undefined)?.[0] ?? ''
    out.push({ text: match[0], kind: `tok-${kind}` })
    last = index + match[0].length
  }
  if (last < source.length) out.push({ text: source.slice(last), kind: '' })
  return out
}
