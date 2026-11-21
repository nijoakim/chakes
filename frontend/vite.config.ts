import { defineConfig } from 'vite'
import path from 'node:path'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.BACKEND_PORT ?? 8000}`,
        ws: true,
      },
    },
  },
})
