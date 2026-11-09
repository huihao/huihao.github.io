/**
 * Compile the Sass sources in src/sass into dist/css.
 *
 * Replaces the old gulp + compass + bower setup. The grid is plain CSS Grid
 * and the breakpoints are plain media queries, so no Sass library is pulled in
 * any more — the only thing PostCSS adds on top of Sass is the browser
 * support layer (autoprefixer + postcss-preset-env).
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
import postcssPresetEnv from 'postcss-preset-env';
import cssnano from 'cssnano';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = path.join(root, 'src', 'sass');
const outDir = path.join(root, 'dist', 'css');

const minify = process.argv.includes('--minify');
const watch = process.argv.includes('--watch');

const sassOptions = {
  style: 'expanded',
  sourceMap: true,
  sourceMapIncludeSources: true,
  // The sources use the Sass module system, but a few remaining @imports in
  // third party partials would still warn.
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

  const plugins = [
    // The modern CSS support layer. Autoprefixer runs on its own below and the
    // custom properties are deliberately left alone: they carry the runtime
    // light/dark theming and must not be inlined.
    postcssPresetEnv({
      stage: 2,
      features: {
        // Autoprefixer runs on its own below.
        autoprefixer: false,
        // The custom properties carry the runtime light/dark theming, they
        // must stay in the output as written.
        'custom-properties': false,
        // `prefers-color-scheme` is used as is.
        'custom-media-queries': false,
        // Sass already compiles the nesting.
        'nesting-rules': false,
        // The site uses media queries as they are, the light/dark pair is
        // handled by the custom properties.
        'light-dark-function': false,
      },
    }),
    autoprefixer(),
  ];
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
