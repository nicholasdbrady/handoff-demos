import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '127.0.0.1',
    strictPort: true,
    proxy: {
      '/demo-api/': {
        target: 'http://127.0.0.1:8765',
        timeout: 360_000,
        proxyTimeout: 360_000,
      },
    },
  },
})
