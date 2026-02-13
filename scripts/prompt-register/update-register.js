#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

function toPosixPath(p) {
  return p.split(path.sep).join(path.posix.sep);
}

async function fileExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function walkDir(dir) {
  const out = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      out.push(...(await walkDir(full)));
    } else {
      out.push(full);
    }
  }
  return out;
}

function parseMetadata(mdText) {
  const lines = mdText.split(/\r?\n/);
  const maxScan = Math.min(lines.length, 80);
  const head = lines.slice(0, maxScan).join('\n');

  const idMatch = head.match(/^PROMPT-ID\s*:\s*(\d{1,3})\s*$/m);
  const verMatch = head.match(/^VERSION\s*:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$/m);
  const titleMatch = head.match(/^TITLE\s*:\s*(.+)\s*$/m);

  if (!idMatch || !verMatch || !titleMatch) return null;

  return {
    id: String(Number(idMatch[1])).padStart(3, '0'),
    version: verMatch[1],
    title: titleMatch[1].trim(),
  };
}

function compareSemverDesc(a, b) {
  const pa = a.split('.').map((n) => Number(n));
  const pb = b.split('.').map((n) => Number(n));
  for (let i = 0; i < 3; i += 1) {
    const d = (pb[i] || 0) - (pa[i] || 0);
    if (d !== 0) return d;
  }
  return 0;
}

async function main() {
  const root = process.cwd();
  const promptsRoot = path.join(root, 'prompts');
  const registerDir = path.join(promptsRoot, 'register');
  const registerPath = path.join(registerDir, 'prompt-register.json');

  if (!(await fileExists(promptsRoot))) {
    console.error('Missing prompts/ directory; nothing to do.');
    process.exit(2);
  }

  await fs.mkdir(registerDir, { recursive: true });
  if (!(await fileExists(registerPath))) {
    await fs.writeFile(registerPath, JSON.stringify({ prompts: [] }, null, 2) + '\n', 'utf8');
  }

  const allFiles = await walkDir(promptsRoot);
  const mdFiles = allFiles
    .filter((p) => p.toLowerCase().endsWith('.md'))
    .filter((p) => !p.startsWith(registerDir + path.sep));

  const entries = [];
  for (const absPath of mdFiles) {
    const rel = path.relative(root, absPath);
    const relPosix = toPosixPath(rel);

    const relToPrompts = path.relative(promptsRoot, absPath);
    const seg = relToPrompts.split(path.sep).filter(Boolean);
    const category = seg.length > 1 ? seg[0] : '';

    const content = await fs.readFile(absPath, 'utf8');
    const meta = parseMetadata(content);
    if (!meta) continue;

    entries.push({
      id: meta.id,
      version: meta.version,
      title: meta.title,
      category,
      path: relPosix,
    });
  }

  const seen = new Set();
  const deduped = [];
  const duplicates = [];
  for (const e of entries) {
    const key = `${e.id}@${e.version}`;
    if (seen.has(key)) {
      duplicates.push(key);
      continue;
    }
    seen.add(key);
    deduped.push(e);
  }

  if (duplicates.length > 0) {
    console.error(`Duplicate prompts detected (same id+version): ${duplicates.join(', ')}`);
    process.exit(3);
  }

  deduped.sort((a, b) => {
    const ida = Number(a.id);
    const idb = Number(b.id);
    if (ida !== idb) return ida - idb;
    return compareSemverDesc(a.version, b.version);
  });

  const outJson = { prompts: deduped };
  await fs.writeFile(registerPath, JSON.stringify(outJson, null, 2) + '\n', 'utf8');
  console.log(`Updated ${toPosixPath(path.relative(root, registerPath))} (${deduped.length} prompts).`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
