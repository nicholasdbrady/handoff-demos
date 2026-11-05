import { defineCodeRunnersSetup } from '@slidev/types'
import { runPython } from '../code-run'

export default defineCodeRunnersSetup(() => ({
  python: code => runPython(code),
  py: code => runPython(code),
}))
