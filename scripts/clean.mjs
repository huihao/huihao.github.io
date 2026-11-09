/**
 * Remove the generated files from dist/.
 *
 * Everything under dist/ is produced by `npm run build` from src/, so it can
 * safely be thrown away and regenerated.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const distDir = path.join(root, 'dist');

for (const dir of ['css', 'img', 'js']) {
  const target = path.join(distDir, dir);
  await fs.rm(target, { recursive: true, force: true });
  console.log(`rm   dist/${dir}`);
}
