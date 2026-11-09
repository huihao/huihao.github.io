# huihao.github.io

My blog — a [Jekyll](https://jekyllrb.com/) site published through GitHub Pages.

The look follows the Apple Human Interface Guidelines: the system font stack,
the iOS system colours in both a light and a dark appearance, translucent
materials, generous corner radii and the spring easing that native apps use.

## Layout

| Path | What it is |
| --- | --- |
| `_posts/` | the blog posts |
| `_layouts/`, `_includes/` | Jekyll templates |
| `index.html`, `article/`, `about.md` | the pages |
| `src/sass/` | Sass sources — `_tokens.scss` holds the design tokens |
| `src/img/` | the images the site uses |
| `dist/css/`, `dist/img/` | build output, committed because GitHub Pages serves the site as plain static files |

## Build

The asset pipeline is plain npm scripts — no gulp, no bower.

```bash
npm install     # install the toolchain
npm run build   # compile src/ -> dist/
npm run dev     # rebuild on change + local server on http://localhost:5050
npm run clean   # remove the generated files in dist/
npm run lint:css   # stylelint over the Sass sources
```

| Script | What it does |
| --- | --- |
| `build:css` | compiles `src/sass/*.scss` into `dist/css/`, then postcss-preset-env + autoprefixer + cssnano |
| `build:css:min` | the same, with cssnano forced on |
| `build:img` | copies `src/img/` into `dist/img/`, re-encoding whatever it can shrink |
| `build:js` | copies `src/js/` into `dist/js/` |
| `watch:css` | rebuilds the css whenever `src/sass/` changes |
| `dev:serve` | browser-sync static server on port 5050 |
| `lint:css` | stylelint with `stylelint-config-standard-scss` |
| `site` | `bundle exec jekyll serve --watch`, the Jekyll site itself (needs Ruby) |

The posts are still written with the `Rakefile` helpers (`rake post["Title"]`),
that part has not changed.

`npm run build` has to be run before pushing: `dist/` is committed, the site
loads `/dist/css/main.css` and `/dist/css/markdown.css` straight from the
repository.

## Design system

Everything visual is driven by the custom properties in
`src/sass/_tokens.scss`:

- `--font-text` / `--font-display` / `--font-mono` — the system stack, so
  macOS and iOS render SF Pro and every other platform its closest match.
- `--label`, `--label-secondary`, `--label-tertiary` — the text colours. They
  are opaque enough to clear WCAG AA (4.5:1) on both backgrounds.
- `--background*`, `--fill*`, `--separator`, `--border` — the surfaces.
  `--background-grouped` is the grouped page the list cards float on,
  `--background` the plain page an article is read on.
- `--material` / `--material-thick` / `--glass-filter` — the translucent
  layers and the refraction recipe of a glass surface.
- `--accent` — the cyan the site has always used, tuned per appearance. It is
  a fill, so the text variant is `--accent-text` (deeper in the light
  appearance, so it clears WCAG AA) with `--accent-text-hover` beside it.
- `--measure` — the width of the reading column, 720px.
- `--media-ratio` — the proportions of the artwork of a post.
- `--space-*`, `--radius-*`, `--duration-*`, `--ease-*` — the 4pt spacing
  grid, the iOS corner radii and the motion.

The dark appearance is a single `prefers-color-scheme` media query away; no
class is toggled in the markup. Icons are drawn from a monochrome sprite and
inverted automatically when the page is dark.

`src/js/site.js` adds the small pieces a native app has and a blog does not:
the reading progress under the top bar, the copy button on every code block,
the reading time under the title, the back to top button, and a fallback for
a cover image that does not load. Everything works without it; the page is
the same, only quieter.
