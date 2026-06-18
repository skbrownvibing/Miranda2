import { defineConfig } from "vitest/config";

export default defineConfig({
  publicDir: false,
  test: {
    include: ["tests/**/*.test.js"],
  },
});
