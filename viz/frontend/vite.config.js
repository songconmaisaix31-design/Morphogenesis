// Build the React shell into fixed, explicit files inside viz/static.
// emptyOutDir stays false so the locked ECharts vendor asset, licenses/ and
// app.js are never touched by a build.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // The iife bundle runs without a module runtime; inline NODE_ENV so no
  // `process` reference survives into the browser.
  define: { 'process.env.NODE_ENV': '"production"' },
  build: {
    outDir: '../static',
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: 'src/shell.jsx',
      formats: ['iife'],
      name: 'MorphFinalsShell',
      cssFileName: 'finals-shell',
    },
    rollupOptions: {
      output: {
        entryFileNames: 'assets/finals-shell.js',
        assetFileNames: 'assets/finals-shell.[ext]',
        // P/T track modules load through import.meta.glob dynamic imports;
        // the iife build must inline them into the single bundle.
        inlineDynamicImports: true,
      },
    },
  },
});
