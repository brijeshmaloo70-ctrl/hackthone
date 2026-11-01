import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: React on :5173, every /api/* call is proxied to the Python backend (server.py on :8000).
// Prod: `npm run build` → dist/ is served directly by server.py on :8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
