import type { Reporter } from "vitest/node";

// Under CI=true a skipped, todo or fails-marked (xfail) test fails the run and is named.
export function noSkipsReporter(): Reporter {
  return {
    onTestRunEnd(modules) {
      const tests = modules.flatMap((m) => [...m.children.allTests()]);
      const skipped = tests.filter((t) => t.result().state === "skipped");
      const xfail = tests.filter(
        (t) => t.options.fails === true && t.result().state !== "skipped",
      );
      const report = (label: string, found: typeof tests) => {
        if (found.length === 0) return;
        const names = found.map((t) => t.fullName).join("\n  ");
        if (process.env.CI === "true") {
          console.error(`${label} tests are not allowed under CI:\n  ${names}`);
          process.exitCode = 1;
        } else {
          console.warn(`warning: ${label.toLowerCase()} tests:\n  ${names}`);
        }
      };
      report("Skipped", skipped);
      report("Fails-marked", xfail);
    },
  };
}
