import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'
import { exec } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    svelte(),
    viteSingleFile(),
    {
      name: 'sync-live-endpoint',
      configureServer(server) {
        server.middlewares.use('/api/sync-live', (req, res) => {
          const scriptPath = path.resolve(__dirname, '../.agent/skills/signupgenius-parser/scripts/sync_signup.py')
          const outPublic = path.resolve(__dirname, './public/nutcracker_data.json')
          const outSrc = path.resolve(__dirname, './src/lib/nutcracker_data.json')
          
          exec(`python3 "${scriptPath}" 10C0C4BA9A929A7FA7-66294307-nutcracker "${outPublic}"`, (error, stdout, stderr) => {
            if (error) {
              res.statusCode = 500
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ success: false, error: error.message }))
              return
            }
            try {
              const fileContent = fs.readFileSync(outPublic, 'utf8')
              fs.writeFileSync(outSrc, fileContent)
              const data = JSON.parse(fileContent)
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ success: true, count: data.length, openCount: data.filter(d => d.isOpen).length, data }))
            } catch (readErr) {
              res.statusCode = 500
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ success: false, error: readErr.message }))
            }
          })
        })
      }
    }
  ],
  build: {
    target: 'esnext',
    assetsInlineLimit: 100000000,
    chunkSizeWarningLimit: 100000000,
    cssCodeSplit: false
  },
  server: {
    port: 5173,
    proxy: {
      '/api/sug': {
        target: 'https://sugapi.signupgenius.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sug/, ''),
        headers: {
          'Origin': 'https://m.signupgenius.com',
          'Referer': 'https://m.signupgenius.com/'
        }
      }
    }
  }
})
