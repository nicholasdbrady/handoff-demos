import { fileURLToPath } from 'node:url'
import { defineConfig, searchForWorkspaceRoot } from 'vite'

export default defineConfig({
  server: {
    host: '127.0.0.1',
    strictPort: true,
    fs: {
      allow: [
        searchForWorkspaceRoot(process.cwd()),
        fileURLToPath(new URL('../shared', import.meta.url)),
      ],
    },
    watch: { ignored: ['**/public/recordings/**', '**/public/task.json'] },
    proxy: {
      '/demo-api/': {
        target: `http://127.0.0.1:${process.env.DEMO_API_PORT || '3071'}`,
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },
})
