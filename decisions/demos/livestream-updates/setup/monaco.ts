import { defineMonacoSetup } from '@slidev/types'

export default defineMonacoSetup(() => ({
  editorOptions: { fontSize: 13, lineHeight: 18, tabSize: 4, lineNumbers: 'on', lineNumbersMinChars: 2 },
}))
