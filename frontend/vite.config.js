import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',  
    manifest: true, 
    rollupOptions: {
      input: path.resolve(__dirname, 'src/main.jsx'),
    },
  },
  server: {
    host: 'localhost',
    port: 5173,
    origin: 'http://localhost:5173',
  },
});

