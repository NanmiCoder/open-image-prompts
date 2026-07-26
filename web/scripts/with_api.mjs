#!/usr/bin/env node
import { createServer as createViteServer, preview } from 'vite'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { createServer as createNetServer } from 'node:net'
import { spawnPython } from '../../scripts/run_python.mjs'

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const repositoryRoot = resolve(webRoot, '..')
const mode = process.argv[2] === 'preview' ? 'preview' : 'dev'

function optionalWebPort(value) {
  if (!value) return undefined
  const port = Number(value)
  if (!Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error(`OIP_WEB_PORT must be an integer between 1 and 65535, received: ${value}`)
  }
  return port
}

// The first start expands an 80 MB archive into a ~270 MB SQLite database and
// warms the gallery filters. That is a couple of seconds on a fast local disk
// but far slower on constrained CI runners, where a 30s budget used to abort a
// start that was still making progress. Readiness is decided by probing /health,
// so a generous ceiling costs nothing when startup is quick.
function startupTimeoutMs() {
  const raw = globalThis.process?.env.OIP_STARTUP_TIMEOUT?.trim()
  if (!raw) return 180_000
  const seconds = Number(raw)
  if (!Number.isFinite(seconds) || seconds <= 0) {
    throw new Error(`OIP_STARTUP_TIMEOUT must be a positive number of seconds, received: ${raw}`)
  }
  return seconds * 1000
}

async function freeLoopbackPort() {
  return new Promise((resolvePromise, reject) => {
    const server = createNetServer()
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      const port = typeof address === 'object' && address ? address.port : 0
      server.close((error) => error ? reject(error) : resolvePromise(String(port)))
    })
  })
}

const apiPort = process.env.OIP_API_PORT || await freeLoopbackPort()
process.env.OIP_API_PORT = apiPort
const api = spawnPython([resolve(repositoryRoot, 'server/oip_api.py')], {
  cwd: repositoryRoot,
  env: { ...process.env, OIP_API_PORT: apiPort },
  stdio: 'inherit',
})

let viteServer
let closing = false

async function waitForApi() {
  const budget = startupTimeoutMs()
  const deadline = Date.now() + budget
  while (Date.now() < deadline) {
    if (api.exitCode !== null) throw new Error(`SQLite API exited with code ${api.exitCode}`)
    try {
      const response = await fetch(`http://127.0.0.1:${apiPort}/health`)
      if (response.ok) return
    } catch {
      // The API is still starting.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100))
  }
  throw new Error(
    `SQLite API did not become ready within ${budget / 1000} seconds. `
    + 'The first start expands the SQLite archive, which is slow on constrained '
    + 'machines; raise OIP_STARTUP_TIMEOUT (seconds) if it needs longer.',
  )
}

async function close(code = 0) {
  if (closing) return
  closing = true
  try {
    await viteServer?.close()
  } finally {
    if (api.exitCode === null) api.kill()
    process.exitCode = code
  }
}

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => void close(0))
}

api.on('exit', (code) => {
  if (!closing) void close(code ?? 1)
})

try {
  await waitForApi()
  // Bind loopback explicitly. Vite's default host is `localhost`, which resolves
  // dual-stack: when another process already holds IPv4 127.0.0.1:5173 Vite can
  // still bind [::1]:5173, skip its port-increment path, and print
  // http://localhost:5173/ — a URL that opens the other application instead of
  // this one. An explicit IPv4 host makes the collision visible so Vite moves to
  // the next free port and prints the port it actually serves.
  const webHost = process.env.OIP_WEB_HOST?.trim() || '127.0.0.1'
  const webPort = optionalWebPort(process.env.OIP_WEB_PORT)
  const webEndpoint = {
    host: webHost,
    // An explicit OIP_WEB_PORT is a contract (Docker, CI, published links):
    // fail loudly rather than drift to a port nobody is watching.
    ...(webPort ? { port: webPort, strictPort: true } : {}),
  }
  viteServer = mode === 'preview'
    ? await preview({ root: webRoot, preview: webEndpoint })
    : await createViteServer({ root: webRoot, server: webEndpoint })
  if (mode === 'dev') await viteServer.listen()
  viteServer.printUrls()
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  await close(1)
}
