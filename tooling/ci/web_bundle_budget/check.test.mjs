import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { gzipSync } from "node:zlib";
import { checkExport, scriptUrls } from "./check.mjs";

test("scriptUrls skips noModule fallbacks and inline scripts", () => {
  const html = `<script src="/a.js" async=""></script>
    <script src="/poly.js" noModule=""></script>
    <script>var x = 1</script><script src="/a.js?v=2"></script>`;
  assert.deepEqual(scriptUrls(html), ["/a.js"]);
});

function exportWith(files) {
  const dir = mkdtempSync(join(tmpdir(), "budget-"));
  mkdirSync(join(dir, "_next"));
  for (const [name, body] of Object.entries(files))
    writeFileSync(join(dir, name), body);
  return dir;
}

test("checkExport counts gzipped bytes per route against the budget", () => {
  const js = Buffer.from("x".repeat(5000) + Math.random());
  const dir = exportWith({
    "index.html": '<script src="/_next/chunk.js"></script>',
    "404.html": "<p>no scripts</p>",
    "_next/chunk.js": js,
  });
  const [home, notFound] = checkExport(dir, gzipSync(js).length)
    .sort((a, b) => a.route.localeCompare(b.route))
    .reverse();
  assert.equal(notFound.bytes, 0);
  assert.equal(home.bytes, gzipSync(js).length);
  assert.equal(home.ok, true);
  assert.equal(
    checkExport(dir, gzipSync(js).length - 1).some((r) => !r.ok),
    true,
  );
});
