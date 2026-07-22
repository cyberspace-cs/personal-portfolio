import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// FastAPI 后端运行在 8000；开发时把 /api 代理过去
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
