import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'

// The "link" between Claude Code and the dashboard:
// Claude / the Rebound plugin writes ~/.rebound/data/tracker.json.
// This middleware serves it live at /api/tracker so the React app can read it
// without any cloud, database, or file-picker — everything stays on the machine.
const DATASTORE = join(homedir(), '.rebound', 'data', 'tracker.json')
const SAMPLE = join(process.cwd(), 'public', 'data', 'tracker.sample.json')

function reboundData() {
  return {
    name: 'rebound-data-middleware',
    configureServer(server) {
      server.middlewares.use('/api/tracker', (req, res) => {
        try {
          const path = existsSync(DATASTORE) ? DATASTORE : SAMPLE
          const json = readFileSync(path, 'utf-8')
          res.setHeader('Content-Type', 'application/json')
          res.setHeader('Cache-Control', 'no-store')
          res.setHeader('X-Rebound-Source', existsSync(DATASTORE) ? 'datastore' : 'sample')
          res.end(json)
        } catch (e) {
          res.statusCode = 500
          res.end(JSON.stringify({ error: String(e) }))
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), reboundData()],
  server: { port: 5273, open: true },
})
