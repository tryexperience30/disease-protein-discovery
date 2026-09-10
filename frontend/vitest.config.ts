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
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
