# huihao.github.io

My blog — a [Jekyll](https://jekyllrb.com/) site published through GitHub Pages.

## Layout

| Path | What it is |
| --- | --- |
| `_posts/` | the blog posts |
| `_layouts/`, `_includes/` | Jekyll templates |
| `index.html`, `article/`, `about.md` | the pages |
| `src/sass/` | Sass sources |
| `src/img/` | the images the site uses |
| `dist/css/`, `dist/img/` | build output, committed because GitHub Pages serves the site as plain static files |

## Build

The asset pipeline is plain npm scripts — no gulp, no bower.

```bash
npm install     # install the toolchain
npm run build   # compile src/ -> dist/
npm run dev     # rebuild on change + local server on http://localhost:5050
npm run clean   # remove the generated files in dist/
```

| Script | What it does |
| --- | --- |
| `build:css` | compiles `src/sass/*.scss` into `dist/css/` and runs autoprefixer over it |
| `build:css:min` | the same, plus cssnano |
| `build:img` | copies `src/img/` into `dist/img/`, compressing whatever it can shrink |
| `build:js` | copies `src/js/` into `dist/js/` |
| `watch:css` | rebuilds the css whenever `src/sass/` changes |
| `dev:serve` | browser-sync static server on port 5050 |
| `site` | `bundle exec jekyll serve --watch`, the Jekyll site itself (needs Ruby) |

The Sass partials — susy, breakpoint-sass and normalize-scss — are npm
dependencies now, so `bower_components/` is no longer needed. The posts are
still written with the `Rakefile` helpers (`rake post["Title"]`), that part has
not changed.

`npm run build` has to be run before pushing: `dist/` is committed, the site
loads `/dist/css/main.css` and `/dist/css/markdown.css` straight from the
repository.
