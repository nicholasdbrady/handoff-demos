import { fileURLToPath } from 'node:url'
import { defineConfig, searchForWorkspaceRoot } from 'vite'

export default defineConfig({
  server: {
    host: '127.0.0.1',
    strictPort: true,
    fs: {
      allow: [
        searchForWorkspaceRoot(process.cwd()),
        fileURLToPath(new URL('../../../shared', import.meta.url)),
      ],
    },
    proxy: {
      '/demo-api/': {
        target: `http://127.0.0.1:${process.env.DEMO_API_PORT || '8765'}`,
        timeout: 360_000,
        proxyTimeout: 360_000,
      },
    },
  },
})
