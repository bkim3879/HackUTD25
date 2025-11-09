import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Use IPv4 to avoid Node resolving localhost to ::1 (IPv6)
      "/workorders": "http://127.0.0.1:8000",
      "/rag": "http://127.0.0.1:8000",
      "/jira": "http://127.0.0.1:8000",
    },
  },
});
