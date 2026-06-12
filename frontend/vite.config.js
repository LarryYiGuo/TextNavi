import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import mkcert from 'vite-plugin-mkcert'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), mkcert()],
  server: {
    host: '0.0.0.0',
    https: true,
    proxy: {
      '/api': {
        // The proxy runs on the dev machine itself, so localhost always
        // reaches the backend no matter which network/IP the Mac is on —
        // no more editing this file when the LAN IP changes.
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
