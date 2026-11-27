// Serves the static export with gzip, the way the edge does, for the browser tests.
// Usage: serve-export.mjs <folder> <port>
import { readFile, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import process from "node:process";
import { URL } from "node:url";
import { gzipSync } from "node:zlib";

const [root, port = "4311"] = process.argv.slice(2);
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".txt": "text/plain",
  ".json": "application/json",
};

createServer(async (req, res) => {
  let path = normalize(
    decodeURIComponent(new URL(req.url, "http://x").pathname),
  );
  if (path.endsWith("/")) path += "index.html";
  const file = join(root, path);
  try {
    if (!(await stat(file)).isFile()) throw new Error("no");
    let body = await readFile(file);
    const ext = extname(file);
    const headers = {
      "content-type": types[ext] ?? "application/octet-stream",
    };
    if (ext !== ".woff2" && body.length > 200) {
      body = gzipSync(body);
      headers["content-encoding"] = "gzip";
    }
    res.writeHead(200, headers);
    res.end(body);
  } catch {
    res.writeHead(404, { "content-type": "text/html" });
    res.end(await readFile(join(root, "404.html")).catch(() => "404"));
  }
}).listen(Number(port), "127.0.0.1");
