import type { Reporter } from "vitest/node";

// Under CI=true a skipped or todo test fails the run and is named.
export function noSkipsReporter(): Reporter {
  return {
    onTestRunEnd(modules) {
      const skipped = modules
        .flatMap((m) => [...m.children.allTests()])
        .filter((t) => t.result().state === "skipped");
      if (skipped.length === 0) return;
      const names = skipped.map((t) => t.fullName).join("\n  ");
      if (process.env.CI === "true") {
        console.error(`Skipped tests are not allowed under CI:\n  ${names}`);
        process.exitCode = 1;
      } else {
        console.warn(`warning: skipped tests:\n  ${names}`);
      }
    },
  };
}
