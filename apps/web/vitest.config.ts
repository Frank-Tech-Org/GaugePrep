import { defineConfig } from "vitest/config";
import { noSkipsReporter } from "./vitest.no-skips";

export default defineConfig({
  test: {
    root: import.meta.dirname,
    testTimeout: 10_000,
    allowOnly: process.env.CI !== "true",
    sequence: { shuffle: true },
    reporters: ["default", noSkipsReporter()],
  },
});
