import type { APIRoute } from 'astro';
import { getPosts, urlOf, descriptionOf } from '../lib/posts';
import { SITE } from '../lib/site';

const escapeXml = (value: string) =>
    value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');

const rfc822 = (date: Date) => date.toUTCString();

export const GET: APIRoute = async (context) => {
    const posts = await getPosts();
    const items = posts.slice(0, 20);
    const latest = items[0];

    const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>${escapeXml(SITE.title)}</title>
    <link>${SITE.url}/</link>
    <description>${escapeXml(SITE.description)}</description>
    <language>${SITE.lang}</language>
    <managingEditor>${escapeXml(SITE.email)}</managingEditor>
    <webMaster>${escapeXml(SITE.email)}</webMaster>
    <pubDate>${rfc822(latest.data.date)}</pubDate>
    <lastBuildDate>${rfc822(new Date())}</lastBuildDate>
    <generator>Astro</generator>
    <ttl>60</ttl>
    <atom:link href="${SITE.url}/feed.xml" rel="self" type="application/rss+xml"/>
${items
    .map((post) => {
        const url = `${SITE.url}${urlOf(post)}`;
        const categories = [...post.data.categories, ...post.data.tags]
            .map((item) => `      <category>${escapeXml(item)}</category>`)
            .join('\n');

        return `    <item>
      <title>${escapeXml(post.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${rfc822(post.data.date)}</pubDate>
      <description>${escapeXml(descriptionOf(post).slice(0, 200))}</description>
      <content:encoded><![CDATA[${post.body.replace(/]]>/g, ']]]]><![CDATA[>')}]]></content:encoded>
${categories}
    </item>`;
    })
    .join('\n')}
  </channel>
</rss>`;

    return new Response(body, {
        headers: { 'Content-Type': 'application/xml; charset=utf-8' },
    });
};
