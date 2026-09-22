// Dev-only build for the standalone preview harness (src/swarm/preview.jsx).
// Never wired into the finals shell build (vite.config.js owns that entry);
// output goes to an OS-temp dir via --outDir so viz/static is untouched:
//   npx vite build --config src/swarm/vite.preview.config.mjs --outDir <tmp>
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': '"production"' },
  build: {
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: { entry: 'src/swarm/preview.jsx', formats: ['iife'], name: 'SwarmPreview', cssFileName: 'swarm-preview' },
    rollupOptions: { output: { entryFileNames: 'swarm-preview.js', assetFileNames: 'swarm-preview.[ext]' } },
  },
});
