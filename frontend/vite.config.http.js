import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// HTTP version for mobile device testing
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    https: false, // Disable HTTPS for mobile testing
    proxy: {
      '/api': {
        target: 'http://172.20.10.3:8001',  // 热点IP地址
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
