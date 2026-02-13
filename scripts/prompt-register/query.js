#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

function normalizeId(id) {
  const s = String(id).trim();
  const n = Number(s);
  if (!Number.isFinite(n)) return null;
  return String(n).padStart(3, '0');
}

function compareSemverDesc(a, b) {
  const pa = String(a).split('.').map((n) => Number(n));
  const pb = String(b).split('.').map((n) => Number(n));
  for (let i = 0; i < 3; i += 1) {
    const d = (pb[i] || 0) - (pa[i] || 0);
    if (d !== 0) return d;
  }
  return 0;
}

async function loadRegister() {
  const root = process.cwd();
  const p = path.join(root, 'prompts', 'register', 'prompt-register.json');
  const txt = await fs.readFile(p, 'utf8');
  const json = JSON.parse(txt);
  return Array.isArray(json?.prompts) ? json.prompts : [];
}

export async function getPromptById(id) {
  const nid = normalizeId(id);
  if (!nid) return null;
  const prompts = await loadRegister();
  return prompts.filter((p) => p.id === nid);
}

export async function getLatestVersion(id) {
  const all = await getPromptById(id);
  if (!all || all.length === 0) return null;
  const sorted = [...all].sort((a, b) => compareSemverDesc(a.version, b.version));
  return sorted[0] || null;
}

export async function listByCategory(category) {
  const c = String(category || '').trim();
  const prompts = await loadRegister();
  return prompts.filter((p) => p.category === c);
}

export async function searchPrompts(keyword) {
  const k = String(keyword || '').trim().toLowerCase();
  if (!k) return [];
  const prompts = await loadRegister();
  return prompts.filter((p) => {
    const hay = `${p.id} ${p.title} ${p.category} ${p.path}`.toLowerCase();
    return hay.includes(k);
  });
}
