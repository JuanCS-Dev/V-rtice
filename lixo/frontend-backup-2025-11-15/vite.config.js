import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { visualizer } from "rollup-plugin-visualizer";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      filename: "dist/stats.html",
    }),
  ],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  resolve: {
    alias: [{ find: "@", replacement: path.resolve(__dirname, "src") }],
  },
  define: {
    // Provide process.env compatibility for libraries that use it
    "process.env": {},
  },
  build: {
    sourcemap: false, // Disable sourcemaps in production
    chunkSizeWarningLimit: 1000, // 1MB warning limit
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React (always needed)
          "vendor-react": ["react", "react-dom", "react/jsx-runtime"],

          // State Management
          "vendor-query": ["@tanstack/react-query"],
          "vendor-store": ["zustand"],

          // Visualization Libraries (HEAVY - lazy load)
          "vendor-maps": ["leaflet", "react-leaflet"],
          "vendor-d3": ["d3"],
          "vendor-charts": ["recharts"],

          // Terminal Emulator (HEAVY - only for MAXIMUS dashboard)
          "vendor-terminal": [
            "@xterm/xterm",
            "@xterm/addon-fit",
            "@xterm/addon-search",
            "@xterm/addon-web-links",
          ],

          // UI Components (frequently used)
          "vendor-ui": [
            "@radix-ui/react-toast",
            "@radix-ui/react-switch",
            "@radix-ui/react-label",
            "@radix-ui/react-slot",
          ],

          // i18n (always needed)
          "vendor-i18n": [
            "i18next",
            "react-i18next",
            "i18next-browser-languagedetector",
          ],

          // Utilities
          "vendor-utils": ["axios", "clsx", "tailwind-merge"],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
