/**
 * 站点配置（对应旧 _config.yml）
 */
export const SITE = {
  title: 'Kimi',
  description: 'huihao 的个人博客，记录 JavaScript、HTML 与 CSS 的实践笔记',
  url: 'https://bio.wuhh.cc',
  email: 'wuhuihao@qq.com',
  lang: 'zh-CN',
  twitterUsername: 'wuhuihao',
  githubUsername: 'huihao',
  author: {
    name: 'Kimi',
    email: 'wuhuihao@qq.com',
    uri: 'https://bio.wuhh.cc',
  },
  /** 每页文章数（与旧站 paginate: 5 一致） */
  perPage: 5,
  /** 评论（giscus，基于 GitHub Discussions），取值来自 https://giscus.app */
  giscus: {
    repo: 'huihao/huihao.github.io',
    repoId: 'MDEwOlJlcG9zaXRvcnkzODU2NTA5MQ==',
    category: 'Announcements',
    categoryId: 'DIC_kwDOAkx0484DK2yc',
    mapping: 'pathname',
    theme: 'preferred_color_scheme',
    lang: 'zh-CN',
  },
} as const;

export const ICONS = {
  favicon: '/favicon.svg',
  faviconIco: '/favicon.ico',
  appleTouch: '/dist/img/apple-touch-icon.png',
  manifest: '/site.webmanifest',
  ogDefault: '/dist/img/og-default.png',
} as const;
