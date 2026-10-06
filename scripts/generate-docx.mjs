#!/usr/bin/env node
// Converts the already-built /cv/ page (dist/cv/index.html) into a Word
// document with pandoc. Like the PDF, the .docx is derived from the web page
// rather than from a separate layout: templates/cv-docx.lua maps the page's
// markup to real Word constructs, and templates/reference.docx supplies the
// Word styles (edit that file in Word to restyle the output).
//
// Run AFTER `npm run pdf` (or `astro build`): this script does not build the
// site, and a later `astro build` clears dist/, which deletes the .docx.

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";

const INPUT_PATH = "dist/cv/index.html";
const OUTPUT_PATH = "dist/cv-thiruvathukal.docx";
const REFERENCE_DOC = "templates/reference.docx";
const FILTER = "templates/cv-docx.lua";

if (!existsSync(INPUT_PATH)) {
  console.error(`${INPUT_PATH} not found - run 'npm run pdf' (or 'npm run build') first.`);
  process.exit(1);
}

try {
  execFileSync("pandoc", ["--version"], { stdio: "ignore" });
} catch {
  console.error("pandoc is required for the Word export (brew install pandoc / apt-get install pandoc).");
  process.exit(1);
}

// The page's <h1> is the name; use it as the Word document Title.
const html = readFileSync(INPUT_PATH, "utf8");
const name = html.match(/<h1[^>]*>(.*?)<\/h1>/s)?.[1].replace(/<[^>]+>/g, "").trim();
if (!name) {
  console.error(`Could not find the <h1> name in ${INPUT_PATH}.`);
  process.exit(1);
}

execFileSync(
  "pandoc",
  [
    "-f", "html",
    "-t", "docx",
    "--reference-doc", REFERENCE_DOC,
    "--lua-filter", FILTER,
    "-M", `title=${name}`,
    "-o", OUTPUT_PATH,
    INPUT_PATH,
  ],
  { stdio: "inherit" },
);

console.log(`Wrote ${OUTPUT_PATH}`);
