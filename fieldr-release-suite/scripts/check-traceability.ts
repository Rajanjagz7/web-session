/**
 * Fails (exit 1) when the specs and src/notes.ts disagree:
 *  - a note with no test of the right kind  (live / fixme / manual)
 *  - a spec that references an id that is not in notes.ts
 *  - a note registered as the wrong kind
 * Nothing in the release notes may be skipped silently.
 */
import fs from 'node:fs';
import path from 'node:path';
import { NOTES, NOTE_BY_ID } from '../src/notes';

const specDir = path.resolve(__dirname, '..', 'src', 'specs');
const files = fs.readdirSync(specDir).filter((f) => f.endsWith('.spec.ts'));
const found = new Map<string, { kind: string; file: string; count: number }[]>();
const re = /\b(live|fixme|manual)\(\s*'([A-Z]{3}-\d{2}[a-z]?)'/g;

for (const file of files) {
  const text = fs.readFileSync(path.join(specDir, file), 'utf8');
  for (const m of text.matchAll(re)) {
    const kind = m[1] ?? '';
    const id = m[2] ?? '';
    const list = found.get(id) ?? [];
    const hit = list.find((x) => x.kind === kind && x.file === file);
    if (hit) hit.count++;
    else list.push({ kind, file, count: 1 });
    found.set(id, list);
  }
}

const problems: string[] = [];
for (const note of NOTES) {
  const hits = found.get(note.id);
  if (!hits) problems.push(`${note.id}: no test registered (expected ${note.kind})`);
  else if (!hits.some((h) => h.kind === note.kind)) problems.push(`${note.id}: registered as ${hits.map((h) => h.kind).join('/')} but notes.ts says ${note.kind}`);
}
for (const id of found.keys()) if (!NOTE_BY_ID.has(id)) problems.push(`${id}: used in a spec but missing from src/notes.ts`);

const kinds = { live: 0, fixme: 0, manual: 0 };
for (const n of NOTES) kinds[n.kind]++;
console.log(`release-note bullets: ${NOTES.length} | live ${kinds.live} | fixme ${kinds.fixme} | manual ${kinds.manual}`);
if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
console.log('traceability OK: every bullet has a test of the declared kind');
