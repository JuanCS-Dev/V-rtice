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
          // Vendor chunks - separate React libs for better caching
          "vendor-react": ["react", "react-dom"],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-maps": ["leaflet", "react-leaflet", "d3"],
          "vendor-ui": [
            "@radix-ui/react-toast",
            "@radix-ui/react-switch",
            "@radix-ui/react-label",
            "@radix-ui/react-slot",
          ],
          "vendor-charts": ["recharts"],
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
