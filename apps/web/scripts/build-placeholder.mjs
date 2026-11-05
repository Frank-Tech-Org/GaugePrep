// Usage: node apps/web/scripts/build-placeholder.mjs <dev|staging> <commit> [outDir]
// Writes index.html into outDir (default apps/web/dist), ready for `wrangler pages deploy`.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { renderPlaceholder } from "../src/placeholder.ts";

const [environment, commit, out] = process.argv.slice(2);
const outDir = resolve(
  out ?? join(dirname(fileURLToPath(import.meta.url)), "..", "dist"),
);

try {
  const html = renderPlaceholder(environment, commit);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);
  process.stdout.write(
    `placeholder for ${environment} at ${commit} written to ${outDir}\n`,
  );
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : error}\n`);
  process.exit(1);
}
