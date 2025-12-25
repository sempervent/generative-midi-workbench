import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        // Always use Docker service name - Vite runs inside container
        target: "http://backend-dev:8000",
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
});
