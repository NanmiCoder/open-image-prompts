import { createReadStream, readFileSync, statSync } from 'node:fs'
import { extname, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const WEB_DIR = fileURLToPath(new URL('.', import.meta.url))
const IMAGE_DIR = resolve(WEB_DIR, '../images')
const DIMS_FILE = resolve(WEB_DIR, 'dims.json')
const API_PORT = globalThis.process?.env.OIP_API_PORT || '8787'
const GALLERY_HMR_PORT = Number(globalThis.process?.env.OIP_GALLERY_HMR_PORT || 0)
const CONTENT_TYPES = {
  '.avif': 'image/avif',
  '.gif': 'image/gif',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
}

function blockPrivateArchive(middlewares) {
  middlewares.use((request, response, next) => {
    const pathname = new URL(request.url || '/', 'http://open-image-prompts.local').pathname
    if (!pathname.startsWith('/db/')) return next()
    response.statusCode = 404
    response.end('Not found')
  })
}

function serveArchiveImages(middlewares) {
  middlewares.use((request, response, next) => {
    const pathname = new URL(request.url || '/', 'http://open-image-prompts.local').pathname
    if (!pathname.startsWith('/images/')) return next()

    let relativePath
    try {
      relativePath = decodeURIComponent(pathname.slice('/images/'.length))
    } catch {
      response.statusCode = 400
      response.end('Bad image path')
      return
    }

    const filePath = resolve(IMAGE_DIR, relativePath)
    if (!filePath.startsWith(`${IMAGE_DIR}${sep}`)) {
      response.statusCode = 403
      response.end('Forbidden')
      return
    }

    try {
      const file = statSync(filePath)
      if (!file.isFile()) return next()
      response.setHeader('Content-Type', CONTENT_TYPES[extname(filePath).toLowerCase()] || 'application/octet-stream')
      response.setHeader('Content-Length', file.size)
      response.setHeader('Cache-Control', 'public, max-age=3600')
      if (request.method === 'HEAD') {
        response.end()
        return
      }
      createReadStream(filePath).pipe(response)
    } catch {
      next()
    }
  })
}

function archiveImagesPlugin() {
  return {
    name: 'open-image-prompts-images',
    configureServer(server) {
      serveArchiveImages(server.middlewares)
    },
    configurePreviewServer(server) {
      serveArchiveImages(server.middlewares)
    },
  }
}

function archiveAssetsPlugin() {
  return {
    name: 'open-image-prompts-assets',
    configureServer(server) {
      blockPrivateArchive(server.middlewares)
    },
    configurePreviewServer(server) {
      blockPrivateArchive(server.middlewares)
    },
    generateBundle() {
      try {
        this.emitFile({
          type: 'asset',
          fileName: 'dims.json',
          source: readFileSync(DIMS_FILE),
        })
      } catch {
        // dims.json is optional (run scripts/export_dims.py to regenerate)
      }
    },
  }
}

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss(), archiveImagesPlugin(), archiveAssetsPlugin()],
  server: {
    hmr: GALLERY_HMR_PORT
      ? { host: '127.0.0.1', clientPort: GALLERY_HMR_PORT }
      : undefined,
    proxy: {
      '/api': `http://127.0.0.1:${API_PORT}`,
      '/health': `http://127.0.0.1:${API_PORT}`,
    },
  },
  preview: {
    proxy: {
      '/api': `http://127.0.0.1:${API_PORT}`,
      '/health': `http://127.0.0.1:${API_PORT}`,
    },
  },
  build: {
    outDir: 'dist',
  },
})
