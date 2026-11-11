/**
 * Remove the generated files.
 *
 * Everything under public/dist, public/pagefind and build/ is produced by
 * `npm run build` from src/, so it can safely be thrown away and regenerated.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const targets = [
  path.join(root, 'public', 'dist'),
  path.join(root, 'public', 'pagefind'),
  path.join(root, 'build'),
];

for (const target of targets) {
  await fs.rm(target, { recursive: true, force: true });
  console.log(`rm   ${path.relative(root, target)}`);
}
