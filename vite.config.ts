import { ecsstatic } from '@acab/ecsstatic/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import checker from 'vite-plugin-checker'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), checker({ typescript: true }), ecsstatic()],
  server: {
    port: 3000,
    open: true,
  },
  build: {
    // minify: false,
  },
})
