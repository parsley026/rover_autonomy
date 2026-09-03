import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/rosbridge': {
        target: 'ws://127.0.0.1:9090',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/rosbridge/, '/'),
      },
    },
  },
})
