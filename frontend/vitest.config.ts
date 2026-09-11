import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  css: {
    postcss: {
      plugins: [],
    },
  },
  test: {
    environment: "node",
    env: {
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
