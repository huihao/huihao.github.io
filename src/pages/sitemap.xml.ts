import type { APIRoute } from 'astro';
import { getPosts, getTranslations, urlOf } from '../lib/posts';

const staticPages = [
    '/',
    '/about/',
    '/article/categories.html',
    '/article/tags.html',
    '/article/archives.html',
    '/article/2/',
    '/article/3/',
];

export const GET: APIRoute = async (context) => {
    const site = String(context.site ?? 'https://bio.wuhh.cc').replace(/\/$/, '');
    const posts = await getPosts();
    const translations = await getTranslations();

    const urls = [
        ...staticPages.map((path) => ({ loc: `${site}${path}`, changefreq: 'weekly' as const })),
        ...[...posts, ...translations].map((post) => ({
            loc: `${site}${urlOf(post)}`,
            lastmod: post.data.date.toISOString(),
            changefreq: 'monthly' as const,
        })),
    ];

    const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
    .map(
        (url) => `  <url>
    <loc>${url.loc}</loc>${
        'lastmod' in url && url.lastmod ? `\n    <lastmod>${url.lastmod}</lastmod>` : ''
    }
    <changefreq>${url.changefreq}</changefreq>
  </url>`,
    )
    .join('\n')}
</urlset>`;

    return new Response(body, {
        headers: { 'Content-Type': 'application/xml; charset=utf-8' },
    });
};
