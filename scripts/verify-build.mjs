/**
 * Verify the built site before it is deployed.
 *
 * Checks that every expected page was generated, that the feeds and the
 * sitemap are well formed, and that every internal link resolves to a file
 * that actually exists. Used by the CI workflow.
 *
 *   node scripts/verify-build.mjs
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const siteDir = path.join(root, 'build');

/** Pages the site must always contain. */
const required = [
  'index.html',
  '404.html',
  'search.html',
  'about/index.html',
  'article/2/index.html',
  'article/3/index.html',
  'article/categories.html',
  'article/tags.html',
  'article/archives.html',
  '2015/07/05/hello.html',
  '2018/10/23/vue-test-unit.html',
  '2026/11/11/ai-battle-royale.html',
  'en/2026/11/11/ai-battle-royale.html',
  'feed.xml',
  'atom.xml',
  'sitemap.xml',
  'pagefind/pagefind.js',
  'dist/css/main.css',
  'dist/css/markdown.css',
  'dist/js/site.js',
  'CNAME',
];

const problems = [];

async function exists(target) {
  return fs.stat(target).then(
    () => true,
    () => false,
  );
}

/** Map a site path to the file that serves it. */
function resolveTarget(url) {
  const clean = url.split('#')[0].split('?')[0];

  if (!clean || clean === '/') return 'index.html';

  const relative = decodeURIComponent(clean.replace(/^\//, ''));

  if (relative.endsWith('/')) return `${relative}index.html`;

  return relative;
}

async function collectHtml(dir, found = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const full = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      await collectHtml(full, found);
    } else if (entry.name.endsWith('.html')) {
      found.push(full);
    }
  }

  return found;
}

for (const file of required) {
  if (!(await exists(path.join(siteDir, file)))) {
    problems.push(`missing page: ${file}`);
  }
}

for (const [file, rootTag] of [
  ['feed.xml', '<rss'],
  ['atom.xml', '<feed'],
  ['sitemap.xml', '<urlset'],
]) {
  const content = await fs.readFile(path.join(siteDir, file), 'utf8');

  if (!content.includes(rootTag)) {
    problems.push(`${file} is not a ${rootTag} document`);
  }

  if (content.includes('//2015') || content.includes('//2026') || content.includes('//article')) {
    problems.push(`${file} contains a double slash in a URL`);
  }
}

const sitemap = await fs.readFile(path.join(siteDir, 'sitemap.xml'), 'utf8');
const locations = sitemap.match(/<loc>/g) ?? [];

if (locations.length < 10) {
  problems.push(`sitemap.xml only lists ${locations.length} URL(s)`);
}

const htmlFiles = await collectHtml(siteDir);
let checked = 0;

for (const file of htmlFiles) {
  const content = await fs.readFile(file, 'utf8');
  const hrefs = content.match(/(?:href|src)="\/[^"]*"/g) ?? [];

  for (const href of hrefs) {
    const url = href.slice(href.indexOf('"') + 1, -1);

    if (url.startsWith('//')) continue;

    const target = path.join(siteDir, resolveTarget(url));

    checked += 1;

    if (!(await exists(target))) {
      problems.push(`${path.relative(siteDir, file)} links to a missing file: ${url}`);
    }
  }
}

if (problems.length > 0) {
  console.error(`verify  ${problems.length} problem(s) found:`);

  for (const problem of problems) console.error(`  - ${problem}`);

  process.exit(1);
}

console.log(`verify  ${htmlFiles.length} HTML page(s), ${locations.length} sitemap URL(s), ${checked} internal link(s) — all good`);
