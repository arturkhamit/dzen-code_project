import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  base: './',
  build: {
    outDir: '../SPA/comments/static/comments/dist',
    emptyOutDir: true,
    rolldownOptions: {
      input: 'src/main.js',
      output: { entryFileNames: 'comments.js', assetFileNames: 'comments.[ext]' },
    },
  },
});
