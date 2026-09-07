import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // En développement, le front appelle /api en relatif et Vite redirige vers le back :
    // pas de CORS à gérer, et aucune URL d'API en dur dans le code.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    restoreMocks: true,
    unstubGlobals: true,
  },
});
