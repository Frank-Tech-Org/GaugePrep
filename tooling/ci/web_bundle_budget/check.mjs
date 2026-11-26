// Fails when the gzipped JS a route's HTML loads grows more than 10% over the home baseline.
// Usage: node tooling/ci/web_bundle_budget/check.mjs <out-dir>
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

export const HOME_BASELINE_BYTES = 138_366;
export const BUDGET_BYTES = Math.round(HOME_BASELINE_BYTES * 1.1);

/** Script URLs a page loads in a modern browser: noModule fallbacks and inline scripts are skipped. */
export function scriptUrls(html) {
  const urls = [];
  for (const [tag] of html.matchAll(/<script\b[^>]*>/gi)) {
    if (/\bnomodule\b/i.test(tag)) continue;
    const src = /\bsrc=["']([^"']+)["']/i.exec(tag)?.[1];
    if (src) urls.push(src.split("?")[0]);
  }
  return [...new Set(urls)];
}

export function routeGzipBytes(html, readAsset) {
  return scriptUrls(html).reduce(
    (total, url) => total + gzipSync(readAsset(url)).length,
    0,
  );
}

function htmlFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory())
      return entry.name === "_next" ? [] : htmlFiles(path);
    return entry.name.endsWith(".html") ? [path] : [];
  });
}

export function checkExport(outDir, budget = BUDGET_BYTES) {
  const readAsset = (url) => readFileSync(join(outDir, url));
  return htmlFiles(outDir).map((file) => {
    const bytes = routeGzipBytes(readFileSync(file, "utf8"), readAsset);
    return { route: relative(outDir, file), bytes, ok: bytes <= budget };
  });
}

function main() {
  const outDir = process.argv[2];
  if (!outDir || !statSync(outDir, { throwIfNoEntry: false })?.isDirectory()) {
    process.stderr.write(
      "Usage: check.mjs <out-dir> (build the web app first)\n",
    );
    process.exit(2);
  }
  const results = checkExport(outDir);
  for (const { route, bytes, ok } of results) {
    process.stdout.write(
      `${ok ? "ok  " : "FAIL"} ${route} ${bytes} B gzip (budget ${BUDGET_BYTES})\n`,
    );
  }
  if (results.some((r) => !r.ok)) process.exit(1);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
