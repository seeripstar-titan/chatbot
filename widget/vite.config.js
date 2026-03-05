import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/chatbot.js"),
      name: "ChatbotWidget",
      fileName: () => "chatbot-widget.js",
      formats: ["iife"],
    },
    outDir: "dist",
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: false,
      },
    },
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        assetFileNames: "chatbot-widget[extname]",
      },
    },
  },
  server: {
    port: 5173,
  },
});
