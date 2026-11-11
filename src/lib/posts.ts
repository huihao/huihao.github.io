import { getCollection, type CollectionEntry } from 'astro:content';
import { SITE } from './site';

export type Post = CollectionEntry<'blog'>;
export type Translation = CollectionEntry<'translations'>;
export type AnyPost = Post | Translation;

/** 文件名去掉日期前缀后就是 URL 里的 slug：2016-12-01-vuex → vuex（Jekyll 会转小写） */
export function slugOf(id: string): string {
  return id
    .replace(/^\d{4}-\d{1,2}-\d{1,2}-/, '')
    .replace(/\.(md|markdown|html)$/, '')
    .toLowerCase();
}

/** 日期取 UTC，和旧站（Jekyll 无时区配置）保持一致 */
export function dateParts(date: Date) {
  return {
    year: date.getUTCFullYear(),
    month: String(date.getUTCMonth() + 1).padStart(2, '0'),
    day: String(date.getUTCDate()).padStart(2, '0'),
  };
}

/**
 * 文章 URL：主稿 /2015/07/05/hello.html，译稿 /en/2026/11/11/xxx.html。
 * front matter 里写了 permalink 的优先（译稿用它固定 /en 前缀）。
 */
export function urlOf(post: AnyPost): string {
  if (post.data.permalink) {
    return post.data.permalink;
  }

  const { year, month, day } = dateParts(post.data.date);
  const prefix = post.data.lang === 'en' ? '/en' : '';

  return `${prefix}/${year}/${month}/${day}/${slugOf(post.id)}.html`;
}

/** 路由参数：/2015/07/05/hello.html → { year, month, day, slug: 'hello.html' } */
export function routeParams(post: AnyPost) {
  const { year, month, day } = dateParts(post.data.date);

  /* 写了 permalink 的文章（译稿）按 permalink 拆路由参数 */
  if (post.data.permalink) {
    const parts = post.data.permalink.replace(/^\//, '').split('/');
    const numbers = parts.slice(-4, -1);

    if (numbers.length === 3 && /^\d{4}$/.test(numbers[0])) {
      return {
        year: numbers[0],
        month: numbers[1],
        day: numbers[2],
        slug: parts[parts.length - 1].replace(/\.html$/, ''),
      };
    }
  }

  return { year: String(year), month, day, slug: slugOf(post.id) };
}

export function formatDate(date: Date, lang: 'zh' | 'en'): string {
  const { year, month, day } = dateParts(date);

  if (lang === 'en') {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return `${months[Number(month) - 1]} ${Number(day)}, ${year}`;
  }

  return `${year}年${month}月${day}日`;
}

export function descriptionOf(post: AnyPost): string {
  const text = post.data.description ?? post.body ?? '';

  return text.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}

export function coverOf(post: AnyPost): string {
  if (post.data.image) {
    return post.data.image;
  }

  return `//whhbio.oss-cn-beijing.aliyuncs.com/blog/${post.data.title}.jpg`;
}

export function categoryOf(post: AnyPost): string {
  return post.data.categories[0] ?? 'note';
}

/** 主稿：按时间倒序 */
export async function getPosts(): Promise<Post[]> {
  const posts = await getCollection('blog');

  return posts.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
}

/** 译稿 */
export async function getTranslations(): Promise<Translation[]> {
  return getCollection('translations');
}

/** 同一篇文章的另一种语言版本 */
/**
 * 找到同一篇文章的另一个语言版本。
 *
 * 候选要同时包含主稿（blog 集合）和译稿（translations 集合）：
 * 中文页的另一个版本在译稿集合里，英文页的另一个版本在主稿集合里。
 */
export function findTranslation(
  post: AnyPost,
  candidates: AnyPost[],
): AnyPost | undefined {
  if (!post.data.translation_key) {
    return undefined;
  }

  const ownUrl = urlOf(post);

  return candidates.find(
    (item) => item.data.translation_key === post.data.translation_key && urlOf(item) !== ownUrl,
  );
}

export function groupCount<T>(items: T[], pick: (item: T) => string[]): Map<string, number> {
  const counts = new Map<string, number>();

  for (const item of items) {
    for (const key of pick(item)) {
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }

  return counts;
}

/** 相关文章：同标签 +3，同分类 +1，取分数最高的 4 篇 */
export function relatedPosts(post: AnyPost, posts: Post[], limit = 4): Post[] {
  const ownUrl = urlOf(post);
  const tags = new Set(post.data.tags);
  const categories = new Set(post.data.categories);

  return posts
    .filter((item) => urlOf(item) !== ownUrl)
    .map((item) => {
      let score = 0;

      for (const tag of item.data.tags) {
        if (tags.has(tag)) {
          score += 3;
        }
      }

      for (const category of item.data.categories) {
        if (categories.has(category)) {
          score += 1;
        }
      }

      return { item, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((entry) => entry.item);
}

/** 上一篇 / 下一篇（posts 已按时间倒序） */
export function neighbours(post: AnyPost, posts: Post[]) {
  const ownUrl = urlOf(post);
  const index = posts.findIndex((item) => urlOf(item) === ownUrl);

  if (index < 0) {
    return { previous: undefined, next: undefined };
  }

  return {
    previous: posts[index + 1],
    next: posts[index - 1],
  };
}

/** 正文词数（中英文混排的粗略统计，用在 JSON-LD 里） */
export function wordCount(body: string): number {
  const cjk = body.match(/[㐀-䶿一-鿿豈-﫿]/g)?.length ?? 0;
  const latin = body.replace(/[㐀-䶿一-鿿豈-﫿]/g, ' ').match(/[A-Za-z0-9]+/g)?.length ?? 0;

  return cjk + latin;
}

export const SITE_URL = SITE.url;
