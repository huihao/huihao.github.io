/**
 * Build the search index.
 *
 * Pagefind crawls the finished site and writes a small index that the search
 * page asks at runtime. GitHub Pages only runs Jekyll, so the index is built
 * here and committed, the same way dist/ is.
 *
 *   npm run build:search
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const siteDir = path.join(root, '.jekyll-site');
const outDir = path.join(root, 'pagefind');

function run(command, args, options = {}) {
  execFileSync(command, args, { cwd: root, stdio: 'inherit', ...options });
}

async function build() {
  console.log('search  building the site with Jekyll');

  await fs.rm(siteDir, { recursive: true, force: true });

  run('jekyll', ['build', '--destination', siteDir], {
    env: { ...process.env, JEKYLL_ENV: 'production' },
  });

  console.log('search  indexing with Pagefind');

  await fs.rm(outDir, { recursive: true, force: true });

  const binary = path.join(root, 'node_modules', '.bin', 'pagefind');

  await fs.mkdir(outDir, { recursive: true });

  run(binary, ['--site', siteDir, '--output-path', outDir, '--root-selector', 'body']);

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
  console.log(`search  the site was built in ${path.relative(root, siteDir)}`);
}

await build();

// The temporary build is not needed any more.
await fs.rm(siteDir, { recursive: true, force: true });
