/**
 * Atom 1.0 订阅源（/atom.xml）
 *
 * @astrojs/rss 只能输出 RSS 2.0，所以这里手写 Atom，
 * 保持和 Jekyll 时代 jekyll-feed 的输出结构一致：
 * 每篇文章一个 entry，正文放在 <content type="html"> 里。
 */
import type { APIRoute } from 'astro';
import { getPosts, urlOf, descriptionOf } from '../lib/posts';
import { SITE } from '../lib/site';

function escapeXml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export const GET: APIRoute = async (context) => {
    const base = String(context.site ?? SITE.url).replace(/\/$/, '');
    const posts = await getPosts();
    const updated = posts[0]?.data.date ?? new Date();

    const entries = posts
        .map((post) => {
            const link = `${base}${urlOf(post)}`;
            const categories = [...post.data.categories, ...post.data.tags]
                .map((name) => `    <category term="${escapeXml(name)}" />`)
                .join('\n');

            return `  <entry>
    <title type="text">${escapeXml(post.data.title)}</title>
    <link href="${link}" rel="alternate" type="text/html" title="${escapeXml(post.data.title)}" />
    <published>${post.data.date.toISOString()}</published>
    <updated>${post.data.date.toISOString()}</updated>
    <id>${link}</id>
    <content type="html" xml:base="${link}">${escapeXml(post.body ?? '')}</content>
    <summary type="text">${escapeXml(descriptionOf(post))}</summary>
${categories}
  </entry>`;
        })
        .join('\n');

    const body = `<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="${SITE.lang}">
  <generator uri="https://astro.build/" version="7.4.10">Astro</generator>
  <link href="${base}/atom.xml" rel="self" type="application/atom+xml" />
  <link href="${base}/" rel="alternate" type="text/html" />
  <updated>${updated.toISOString()}</updated>
  <id>${base}/</id>
  <title type="text">${escapeXml(SITE.title)}</title>
  <subtitle>${escapeXml(SITE.description)}</subtitle>
  <author>
    <name>${escapeXml(SITE.author.name)}</name>
    <email>${escapeXml(SITE.author.email)}</email>
    <uri>${escapeXml(SITE.author.uri)}</uri>
  </author>
${entries}
</feed>
`;

    return new Response(body, {
        headers: { 'Content-Type': 'application/atom+xml; charset=utf-8' },
    });
};
