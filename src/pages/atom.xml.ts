import type { APIRoute } from 'astro';
import rss from '@astrojs/rss';
import { getPosts, urlOf, descriptionOf } from '../lib/posts';
import { SITE } from '../lib/site';

export const GET: APIRoute = async (context) => {
    const posts = await getPosts();

    return rss({
        title: SITE.title,
        description: SITE.description,
        site: context.site ?? SITE.url,
        trailingSlash: false,
        items: posts.map((post) => ({
            title: post.data.title,
            description: descriptionOf(post),
            pubDate: post.data.date,
            link: urlOf(post),
            categories: [...post.data.categories, ...post.data.tags],
            content: post.body,
        })),
        customData: `<language>${SITE.lang}</language>`,
    });
};
