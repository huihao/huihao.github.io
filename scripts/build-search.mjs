/**
 * Build the search index.
 *
 * Pagefind crawls the finished site and writes a small index that the search
 * page asks at runtime. The index is built here and copied into public/,
 * the same way the compiled CSS and images are.
 *
 *   npm run build:search
 *
 * Set PAGEFIND_SKIP=1 to reuse an index that is already present in
 * public/pagefind (used by CI, where the index is restored from the Actions
 * cache and only needs rebuilding when the content actually changed).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const siteDir = path.join(root, 'build');
const outDir = path.join(root, 'public', 'pagefind');

function run(command, args, options = {}) {
  execFileSync(command, args, { cwd: root, stdio: 'inherit', ...options });
}

async function exists(target) {
  return fs.stat(target).then(
    () => true,
    () => false,
  );
}

async function build() {
  console.log('search  building the site with Astro');

  await fs.rm(siteDir, { recursive: true, force: true });

  run(process.execPath, [path.join(root, 'node_modules', 'astro', 'bin', 'astro.mjs'), 'build'], {
    env: { ...process.env, NODE_ENV: 'production' },
  });

  /* The Astro build copies public/ into build/, so a restored index is already
     part of the output; only the index itself is left to do. */
  const reusable = process.env.PAGEFIND_SKIP === '1' || process.env.PAGEFIND_SKIP === 'true';

  if (reusable && (await exists(path.join(outDir, 'pagefind.js')))) {
    console.log('search  reusing the existing Pagefind index');
    await fs.cp(outDir, path.join(siteDir, 'pagefind'), { recursive: true, force: true });

    return;
  }

  console.log('search  indexing with Pagefind');

  await fs.rm(outDir, { recursive: true, force: true });

  const binary = path.join(root, 'node_modules', '.bin', 'pagefind');

  await fs.mkdir(outDir, { recursive: true });

  run(binary, ['--site', siteDir, '--output-path', outDir, '--root-selector', 'body']);

  /* The Astro build already copied public/ into build/, but the index is
     generated afterwards — copy it over so the deployable site has it. */
  await fs.cp(outDir, path.join(siteDir, 'pagefind'), { recursive: true });

  const files = await fs.readdir(outDir, { recursive: true });
  const bytes = (
    await Promise.all(
      files
        .filter((file) => typeof file === 'string')
        .map(async (file) => {
          const stat = await fs.stat(path.join(outDir, file)).catch(() => null);

          return stat && stat.isFile() ? stat.size : 0;
        }),
    )
  ).reduce((total, size) => total + size, 0);

  console.log(`search  ${files.length} file(s) -> ${path.relative(root, outDir)} (${bytes} bytes)`);
}

await build();
