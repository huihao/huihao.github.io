# huihao.github.io

> Kimi 的个人博客 —— 用 **Astro** 构建，样式遵循 **Apple Human Interface Guidelines**。

博客从 Jekyll 迁移到 Astro（2026-11）：URL 结构、页面结构、RSS 订阅源全部保持不变，
旧链接和订阅地址继续可用。

- 站点：<https://bio.wuhh.cc>
- 仓库：<https://github.com/huihao/huihao.github.io>

## 技术栈

| 部分 | 选型 |
| --- | --- |
| 框架 | Astro 7（静态输出，`output: 'static'`） |
| 样式 | Sass + PostCSS + Autoprefixer + CSSNano（无 Grid/Breakpoint 依赖） |
| 高亮 | Shiki 双主题（`github-light-high-contrast` / `github-dark-high-contrast`，随明暗模式切换，对比度达 WCAG AA） |
| 搜索 | Pagefind（构建时索引，产物在 `public/pagefind/`） |
| 评论 | giscus（GitHub Discussions） |
| 订阅源 | 手写 RSS 2.0（`/feed.xml`）+ 手写 Atom 1.0（`/atom.xml`） |
| 部署 | GitHub Actions → GitHub Pages |

## 快速开始

```bash
npm install
npm run dev       # 本地预览 http://localhost:4321
npm run build     # 生成 build/
npm run preview   # 预览 build/
```

## 构建脚本

| 命令 | 作用 |
| --- | --- |
| `npm run build:css` | `src/sass/*.scss` → `public/dist/css/*.css`（含 sourcemap） |
| `npm run build:img` | `src/img/*` → `public/dist/img/`（sharp 压缩，只在变小时才替换） |
| `npm run build:js` | `src/js/*` → `public/dist/js/` |
| `npm run build:assets` | 生成 favicon / apple-touch-icon / og 图标 |
| `npm run build:site` | `astro build` → `build/` |
| `npm run build:search` | 构建站点并用 Pagefind 生成 `public/pagefind/` |
| `npm run build` | 依次执行 css / img / js / assets / search（含站点构建） |
| `npm run clean` | 删除 `public/dist`、`public/pagefind`、`build/` |
| `npm run lint:css` | stylelint 检查 SCSS |
| `npm run verify` | 检查 `build/` 产物：必备页面、订阅源、站内链接是否齐全 |

## 目录结构

```
src/
  components/     Header / Footer / Sidebar / Card / Toc / PostNav / Comments …
  content/
    blog/         主稿（Markdown）
    translations/ 译稿（Markdown，默认不进入列表与订阅源）
  layouts/        BaseLayout（列表页）、PostLayout（文章页）
  lib/            site.ts（站点常量）、posts.ts（文章数据处理）
  pages/          路由：index、article/[page]、article/categories|tags|archives、
                  about、search、404、feed.xml、atom.xml、sitemap.xml
  sass/           设计令牌与组件样式
  js/             site.js（主题切换、阅读进度、复制按钮、目录、阅读时长…）
scripts/          构建脚本
public/           静态资源（CNAME、webmanifest、dist/、pagefind/）
```

## 写作

文章放在 `src/content/blog/`，译稿放在 `src/content/translations/`。

```yaml
---
title: 文章标题
date: 2018-10-23 12:00:00
description: 一句话摘要，会用在卡片和 meta description 上
categories: [javascript]
tags: [作用域, javascript]
lang: zh          # zh（默认）或 en
translation_key:  # 同一篇的另一个语言版本共用
image: /dist/img/cover-xxx.png
---
```

- 代码块请标注语言：```` ```js ```` → Shiki 会高亮，复制按钮也会显示语言名。
- 译稿用 `translation_key` 与主稿配对，文章页会出现语言切换，列表页不会出现重复条目。
- URL 规则：主稿 `/YYYY/MM/DD/slug.html`，译稿 `/en/YYYY/MM/DD/slug.html`。

## 视觉与材质

站点的视觉变量全部集中在 `src/sass/_tokens.scss`，改配色和材质只需要改这一处。

- **毛玻璃**：`src/sass/_theme.scss` 里的 `glass` / `glass-strong` / `glass-subtle`
  混入是唯一的玻璃入口——半透明填充 + `saturate() blur()` 折射背后内容 +
  顶部一道高光内阴影 + 一层柔和投影。列表卡片、侧栏分组、目录、上下篇、
  相关文章、标签、分页按钮、搜索框、分享菜单和 404 面板都用它；
  不支持 `backdrop-filter` 的浏览器自动退回不透明面板。
- **背景**：页面背后有一层彩色光晕（`#wrapper::before`）和一层 28px 的
  点阵网格（`#wrapper::after`），玻璃才有东西可以折射；网格也是整站的
  蓝图底纹。
- **等宽细节**：日期、阅读时长、标签、目录标题、上下篇标签、分页计数、
  分类计数、代码块语言名和订阅源链接都用 `var(--font-mono)`，代码块还有
  一条编辑器风格的头部栏（左侧语言、右侧复制）。
- **列表**：首页只有一篇头条（最新一篇，带封面），其余文章收进一块毛玻璃分组列表，
  每行只有「分类 · 日期」的小标、标题和一行摘要，靠发丝线分隔；
  「阅读全文」胶囊与列表封面都已去掉。
- **其它**：标题 `text-wrap: balance`、正文 `text-wrap: pretty`、
  锚点标题留出 `scroll-margin-top` 避开吸顶栏、细滚动条、
  `prefers-reduced-motion` 下关闭平滑滚动。

## 明暗模式

站点跟随系统偏好，也可以右上角一键切换。切换结果存在 `localStorage`，
`<head>` 里的内联脚本在首次绘制前就决定主题，所以不会闪烁。

## 分享

文章页标题下方有「分享」按钮（`src/components/Share.astro`）：

- 手机等支持 **Web Share API** 的浏览器会直接调起系统原生的分享面板，
  里面就是访客安装的 X、微信、信息等应用，不用跳转；
- 桌面浏览器没有原生面板，会展开一个小菜单：X（`https://x.com/intent/post`，
  X 现在的分享地址）、微博，以及「复制链接」；
- 不启用脚本时菜单仍然显示（`<noscript>` 里的样式兜底），X 和微博是普通链接。

## 订阅源

- RSS 2.0：<https://bio.wuhh.cc/feed.xml>
- Atom：<https://bio.wuhh.cc/atom.xml>

## 部署与 CI

| 工作流 | 触发 | 作用 |
| --- | --- | --- |
| `.github/workflows/deploy.yml` | 推送到 `master` | lint → 构建 → 校验产物 → 发布到 GitHub Pages |
| `.github/workflows/ci.yml` | Pull Request / 手动 | lint → 构建 → 校验产物，不发布 |

- **Pagefind 索引缓存**：搜索索引只随内容变化，所以缓存键由 `src/content`、`src/pages`、
  `src/components`、`src/layouts`、`src/lib`、`astro.config.mjs` 和 `package-lock.json`
  的哈希生成；缓存命中时通过 `PAGEFIND_SKIP=1` 复用索引，跳过重新索引。
- **产物校验**：`npm run verify` 会确认必备页面都生成了、订阅源与 sitemap 格式正确，
  并且页面里 800+ 条站内链接都能找到对应文件，避免把坏链接发布出去。

> 首次启用前，请在仓库 **Settings → Pages → Build and deployment → Source** 中
> 选择 **GitHub Actions**（原来的 "Deploy from a branch" 指向的 Jekyll 构建已经不再产出站点）。

## 许可证

文章内容与代码均保留原仓库的许可。
