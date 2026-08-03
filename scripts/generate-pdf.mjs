#!/usr/bin/env node
// Builds the site, serves the static output, and prints the /cv/ route to a
// PDF via headless Chrome - the "beautiful PDF" is literally a screenshot of
// the web page's print stylesheet, so there is only one layout to maintain.
//
// The site is fully static, so it's served with a tiny in-process HTTP
// server rather than spawning `astro preview` as a subprocess - one less
// process whose shutdown we'd otherwise have to depend on.

import { chromium } from "playwright";
import { execSync } from "node:child_process";
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";

const PORT = 4173;
const ROOT = path.resolve("dist");
const OUTPUT_PATH = "dist/cv-thiruvathukal.pdf";

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

function startStaticServer(root, port) {
  const server = http.createServer(async (req, res) => {
    let urlPath = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    if (urlPath.endsWith("/")) urlPath += "index.html";
    const filePath = path.join(root, urlPath);

    if (!filePath.startsWith(root)) {
      res.writeHead(403).end();
      return;
    }

    try {
      const data = await readFile(filePath);
      const contentType = MIME_TYPES[path.extname(filePath)] ?? "application/octet-stream";
      res.writeHead(200, { "Content-Type": contentType }).end(data);
    } catch {
      res.writeHead(404).end("Not found");
    }
  });

  return new Promise((resolve) => {
    server.listen(port, () => resolve(server));
  });
}

async function main() {
  console.log("Building site...");
  execSync("npx astro build", { stdio: "inherit" });

  console.log("Starting static file server...");
  const server = await startStaticServer(ROOT, PORT);

  try {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto(`http://localhost:${PORT}/cv/`, { waitUntil: "networkidle" });
    await page.emulateMedia({ media: "print" });
    await page.pdf({
      path: OUTPUT_PATH,
      format: "Letter",
      printBackground: true,
      margin: { top: "0.6in", bottom: "0.6in", left: "0.6in", right: "0.6in" },
    });
    await browser.close();

    console.log(`Wrote ${OUTPUT_PATH}`);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
