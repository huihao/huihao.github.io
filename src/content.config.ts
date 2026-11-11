import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * 站点内容分两个集合：
 *
 * - blog：主稿（首页列表、分页、RSS/Atom、sitemap 都只统计它）
 * - translations：同一篇文章的其他语言版本（不在首页重复出现，
 *   通过 translation_key 与主稿配对，文章页用语言切换器互相跳转）
 */

const list = z
  .union([z.string(), z.array(z.string())])
  .transform((value) => (Array.isArray(value) ? value : [value]));

const fields = z.object({
  title: z.string(),
  description: z.string().optional(),
  date: z.coerce.date(),
  lang: z.enum(['zh', 'en']).default('zh'),
  categories: list.default([]),
  tags: list.default([]),
  translation_key: z.string().optional(),
  image: z.string().optional(),
  permalink: z.string().optional(),
});

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: fields,
});

const translations = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/translations' }),
  schema: fields,
});

export const collections = { blog, translations };
