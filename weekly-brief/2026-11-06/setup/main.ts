import { defineAppSetup } from '@slidev/types'
import '@fontsource-variable/ibm-plex-sans'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'
import '@fontsource/ibm-plex-mono/700.css'
import '../style.css'
import '../visuals.css'

export default defineAppSetup(() => {
  const policy = document.createElement('meta')
  policy.httpEquiv = 'Content-Security-Policy'
  // A child sandbox alone does not prevent navigation within that child.
  policy.content = "frame-src 'self'; object-src 'none'"
  document.head.prepend(policy)
})
