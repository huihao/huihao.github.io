import { defineConfig } from 'astro/config';

/**
 * Astro 配置
 *
 * - site：站点主域（CNAME 指向 bio.wuhh.cc），用于生成绝对链接、canonical、RSS
 * - outDir：构建产物目录（与 public/dist 的静态资源目录分开，避免相互覆盖）
 * - build.format: 'preserve'：保持与 Jekyll 时代完全一致的 URL 结构
 *   （/2015/07/05/hello.html、/article/2/、/article/categories.html …），
 *   这样旧链接、订阅源和搜索引擎收录都不会失效。
 */
export default defineConfig({
  site: 'https://bio.wuhh.cc',
  outDir: './build',
  trailingSlash: 'ignore',
  build: {
    format: 'preserve',
  },
  /**
   * Astro 会把动态路由参数转成小写，而旧站是大小写敏感的：
   * /2017/01/02/JavaScript-scopr.html 在 Jekyll 时代是可访问的。
   * 这里补一个静态重定向页保住老链接。
   */
  redirects: {
    '/2017/01/02/JavaScript-scopr': '/2017/01/02/javascript-scopr.html',
  },
  markdown: {
    shikiConfig: {
      themes: {
        light: 'github-light-high-contrast',
        dark: 'github-dark-high-contrast',
      },
      defaultColor: false,
      wrap: true,
      transformers: [
        {
          name: 'language-class',
          pre(node, meta) {
            if (meta?.lang) {
              node.properties.class = `${node.properties.class ?? ''} language-${meta.lang}`;
            }
          },
        },
      ],
    },
  },
});
