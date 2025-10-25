import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@features': path.resolve(__dirname, './src/features'),
      '@store': path.resolve(__dirname, './src/store'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
    },
  },
  server: {
    watch: {
      usePolling: true, // Required for WSL2 and Docker on Windows
      interval: 1000,   // Poll every 1 second
    },
    host: true, // Needed for Docker
    strictPort: true,
    port: 5173,
  },
})
