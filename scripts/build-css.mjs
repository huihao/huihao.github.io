/**
 * Compile the Sass sources in src/sass into dist/css.
 *
 * Replaces the old gulp + compass + bower setup. The Sass library partials
 * (susy, breakpoint-sass, normalize-scss) are now regular npm dependencies and
 * are resolved through `loadPaths` instead of bower_components.
 *
 *   node scripts/build-css.mjs             # expanded output + autoprefixer
 *   node scripts/build-css.mjs --minify    # additionally run cssnano
 *   node scripts/build-css.mjs --watch     # rebuild on change
 */
import fs from 'node:fs/promises';
import { watch as watchFs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as sass from 'sass';
import postcss from 'postcss';
import autoprefixer from 'autoprefixer';
import cssnano from 'cssnano';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = path.join(root, 'src', 'sass');
const outDir = path.join(root, 'dist', 'css');

const loadPaths = [
  path.join(root, 'node_modules', 'susy', 'sass'),
  path.join(root, 'node_modules', 'breakpoint-sass', 'stylesheets'),
  path.join(root, 'node_modules', 'normalize-scss', 'sass'),
];

const minify = process.argv.includes('--minify');
const watch = process.argv.includes('--watch');

const sassOptions = {
  loadPaths,
  style: 'expanded',
  sourceMap: true,
  sourceMapIncludeSources: true,
  // susy 2 and breakpoint-scss 2 are not maintained and still use @import,
  // slash-as-division and the old if() function. They work fine, they are
  // just noisy.
  silenceDeprecations: ['import', 'slash-div', 'global-builtin', 'color-functions', 'if-function'],
};

async function entryFiles() {
  const files = await fs.readdir(srcDir);
  return files
    .filter((file) => file.endsWith('.scss') && !file.startsWith('_'))
    .sort();
}

async function buildOne(file) {
  const from = path.join(srcDir, file);
  const to = path.join(outDir, file.replace(/\.scss$/, '.css'));

  const compiled = sass.compile(from, sassOptions);

  // sass reports absolute file:// urls as map sources. Rewrite them relative to
  // the entry file so the committed maps stay machine independent.
  const prevMap = { ...compiled.sourceMap };
  prevMap.sources = compiled.sourceMap.sources.map((source) => {
    const filePath = source.startsWith('file://') ? fileURLToPath(source) : source;
    return path.relative(path.dirname(from), filePath).split(path.sep).join('/');
  });

  const plugins = [autoprefixer()];
  if (minify) plugins.push(cssnano({ preset: 'default' }));

  const result = await postcss(plugins).process(compiled.css, {
    from,
    to,
    map: {
      prev: JSON.stringify(prevMap),
      inline: false,
      annotation: true,
    },
  });

  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(to, result.css.endsWith('\n') ? result.css : `${result.css}\n`);
  if (result.map) await fs.writeFile(`${to}.map`, result.map.toString());
  return to;
}

async function buildAll() {
  const files = await entryFiles();
  for (const file of files) {
    const out = await buildOne(file);
    console.log(`css  ${path.relative(root, out)}`);
  }
  return files;
}

await buildAll();

if (watch) {
  let timer;
  const rebuild = () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      try {
        await buildAll();
      } catch (error) {
        console.error(`sass error: ${error.message}`);
      }
    }, 100);
  };

  // `fs.watch` from node:fs/promises is an async iterator and silently ignores
  // the recursive option, so the callback based watcher from node:fs is used
  // here. Recursive watching is not available on every platform, hence the
  // fallback that watches the files one by one.
  const watchers = [];
  const add = (target, options) => {
    const watcher = watchFs(target, options, rebuild);
    watcher.on('error', (error) => {
      console.error(`watch error on ${path.relative(root, target)}: ${error.message}`);
      watcher.close();
    });
    watchers.push(watcher);
  };

  const watchIndividually = async () => {
    for (const file of await fs.readdir(srcDir)) {
      add(path.join(srcDir, file));
    }
  };

  try {
    add(srcDir, { recursive: true });
  } catch (error) {
    console.warn(`recursive watch unavailable (${error.message}), watching the files one by one`);
    await watchIndividually();
  }

  console.log('watching src/sass for changes...');
}
