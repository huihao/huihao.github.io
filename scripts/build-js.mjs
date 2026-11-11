/**
 * Copy the scripts in src/js into dist/js.
 *
 * Replaces the old `gulp-jshint` + copy task. There is currently no
 * src/js directory, the step is kept so that adding JavaScript later works
 * the same way it did before.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = path.join(root, 'src', 'js');
const outDir = path.join(root, 'public', 'dist', 'js');

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(full)));
    else files.push(full);
  }
  return files;
}

async function build() {
  let files;
  try {
    files = await walk(srcDir);
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.log('js   no src/js directory, nothing to do');
      return;
    }
    throw error;
  }

  for (const file of files) {
    const target = path.join(outDir, path.relative(srcDir, file));
    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.copyFile(file, target);
  }

  console.log(`js   ${files.length} file(s) -> ${path.relative(root, outDir)}`);
}

await build();
