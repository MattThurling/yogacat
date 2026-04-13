import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import url from '@rollup/plugin-url'

export default defineConfig({
  assetsInclude: ['**/*.m4a'],
  plugins: [
    vue(),
    tailwindcss(),
  ],
  build: {
    outDir: '../static/dist',  // Output directory for Django to use
    emptyOutDir: true,
    rollupOptions: {
      input: './src/main.js',
      // Since Python collectstatic handles manifests, there is no need to add unique ids
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]'
      },
      plugins: [
        url({
          include: ['**/*.mp3', '**/*.ogg', '**/*.wav', '**/*.m4a'],
          limit: 0, // Always copy to output folder instead of inline as data URI
          fileName: 'assets/[name][extname]',
        }),
      ],
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    proxy: {
      '/api': 'http://sfl.local:8000'
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const origin = req.headers.origin;
        if (origin && origin.endsWith('.sfl.local:8000')) {
          res.setHeader('Access-Control-Allow-Origin', origin)
          res.setHeader('Access-Control-Allow-Credentials', 'true')
        }
        next()
      })
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
  }
})