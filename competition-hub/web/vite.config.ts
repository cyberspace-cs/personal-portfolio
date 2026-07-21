import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发时把 /api 代理到本地 FastAPI 后端（默认 8000）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
