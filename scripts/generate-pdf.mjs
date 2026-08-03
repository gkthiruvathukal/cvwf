#!/usr/bin/env node
// Builds the site, serves the static output, and prints the /cv/ route to a
// PDF via headless Chrome - the "beautiful PDF" is literally a screenshot of
// the web page's print stylesheet, so there is only one layout to maintain.

import { chromium } from "playwright";
import { spawn, execSync } from "node:child_process";

const PORT = 4173;
const OUTPUT_PATH = "dist/cv-thiruvathukal.pdf";

function waitForServer(url, timeoutMs = 20000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = async () => {
      try {
        const res = await fetch(url);
        if (res.ok) return resolve();
      } catch {
        // not up yet
      }
      if (Date.now() - start > timeoutMs) {
        return reject(new Error(`Server at ${url} did not start in time`));
      }
      setTimeout(attempt, 300);
    };
    attempt();
  });
}

async function main() {
  console.log("Building site...");
  execSync("npx astro build", { stdio: "inherit" });

  console.log("Starting preview server...");
  const server = spawn(
    "npx",
    ["astro", "preview", "--port", String(PORT)],
    { stdio: "pipe" },
  );

  try {
    await waitForServer(`http://localhost:${PORT}/`);

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
    server.kill();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
