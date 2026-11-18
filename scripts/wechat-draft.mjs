#!/usr/bin/env node
/**
 * 把站内 Markdown 文章转成微信公众号「草稿箱」图文（draft/add）。
 *
 *   node scripts/wechat-draft.mjs                 # 只生成本地 HTML 预览，不联网
 *   node scripts/wechat-draft.mjs --publish       # 上传封面 + 写入公众号草稿箱
 *   node scripts/wechat-draft.mjs --check         # 只校验 AppID/AppSecret 与 access_token
 *
 * 凭据（不要写进仓库、不要贴进聊天）：
 *   环境变量  WECHAT_APP_ID / WECHAT_APP_SECRET
 *   或文件    ~/.config/wechat-publish/credentials.json  {"appid":"...","appsecret":"..."}
 *
 * 公众号后台需要把本机公网 IP 加进「设置与开发 → 基本配置 → IP 白名单」，
 * 否则 access_token 接口会返回 errcode 40164。
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { marked, Renderer } from 'marked';
import sharp from 'sharp';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WECHAT_DIR = path.join(ROOT, 'drafts/ai-frontend-role-evolution/wechat');
const OUT_DIR = path.join(WECHAT_DIR, 'out');
const CRED_FILE = path.join(os.homedir(), '.config/wechat-publish/credentials.json');
const TOKEN_CACHE = path.join(os.homedir(), '.cache/wechat-publish/token.json');

const DEFAULTS = {
  src: 'src/content/blog/2026-11-17-ai-frontend-role-evolution.md',
  sourceUrl: 'https://bio.wuhh.cc/2026/11/17/ai-frontend-role-evolution.html',
  thumb: path.join(WECHAT_DIR, 'cover-1-1.svg'),
};

/** 公众号正文上限约 20000 字（含 HTML 标记），超了会被接口拒。 */
const CONTENT_LIMIT = 20000;

/** 微信编辑器只认 inline style，不认 <style> 与 class。样式串尽量短，否则正文体积翻几倍。 */
const S = {
  p: 'font-size:16px;line-height:1.85;color:#3f3f3f;margin:0 0 18px;',
  h2: 'font-size:20px;font-weight:700;color:#1a1a1a;line-height:1.5;margin:40px 0 20px;padding-left:10px;border-left:4px solid #20c6f2;',
  h3: 'font-size:17px;font-weight:700;color:#1a1a1a;line-height:1.6;margin:28px 0 14px;',
  strong: 'font-weight:700;color:#0a6b8f;',
  em: 'font-style:normal;color:#3f3f3f;',
  code: 'font-family:Menlo,Consolas,monospace;font-size:14px;background:#f2f3f5;color:#c7254e;padding:2px 5px;',
  ul: 'margin:0 0 18px;padding-left:22px;',
  ol: 'margin:0 0 18px;padding-left:22px;',
  li: 'font-size:16px;line-height:1.85;color:#3f3f3f;margin:0 0 10px;',
  hr: 'margin:34px 0;border:none;border-top:1px solid #e8eaed;',
  quoteCard:
    'margin:22px 0;padding:14px 16px;border-left:3px solid #20c6f2;background:#f4f8fa;border-radius:0 6px 6px 0;',
  quoteCardP: 'font-size:15px;line-height:1.8;color:#4a4a4a;margin:0;',
  quotePlainP: 'font-size:15px;line-height:1.85;color:#6b6b6b;margin:0 0 16px;',
  card: 'margin:20px 0;padding:4px 0;',
};

/** 这 7 段引用做成带竖线的引用卡，其余降级成灰色普通段落。 */
const HERO_QUOTES = [
  '当 90% 代码由 AI 生成', // 美团 A1 的结论句
  'AI 把瓶颈从', // 美团 A2 三连
  '压测智能分析', // 得物技术
  '监控一片绿', // Harness 复盘
  '先用 AI 替代别人', // 晚点
  '有 30 个原本会出现的岗位没有出现', // 虎嗅·隐形岗位
  '岗位在缩，价值在移', // 结语
];
const squash = (s) => String(s).replace(/\s+/g, '');

const escapeHtml = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const stripFrontmatter = (md) => {
  const m = md.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n/);
  return m ? md.slice(m[0].length) : md;
};

/** 站内互链在公众号里点不动，换成一句描述；正文外链统一清成纯文本。 */
function preprocess(md) {
  return md.replace(
    /可以接着看站内那篇\s*\[《AI 发展下的互联网开发圈现在就是一场大逃杀》\]\(\/2026\/11\/11\/ai-battle-royale\.html\)/g,
    '站内另一篇讲个人行动清单的《AI 发展下的互联网开发圈现在就是一场大逃杀》',
  );
}

function parseFrontmatter(md) {
  const m = md.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!m) return {};
  const out = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (!kv) continue;
    let value = kv[2].trim();
    if (
      (value.startsWith("'") && value.endsWith("'")) ||
      (value.startsWith('"') && value.endsWith('"'))
    ) {
      value = value.slice(1, -1);
    }
    out[kv[1]] = value;
  }
  return out;
}

const renderer = new Renderer();
Object.assign(renderer, {
  heading(token) {
    const text = this.parser.parseInline(token.tokens);
    return token.depth <= 2
      ? `<h2 style="${S.h2}">${text}</h2>`
      : `<p style="${S.h3}">${text}</p>`;
  },
  paragraph(token) {
    const strongs = token.tokens.filter((t) => t.type === 'strong');
    const solo = strongs.length === 1 && token.tokens.length === 1;
    this._keepBold = solo;
    const html = this.parser.parseInline(token.tokens);
    this._keepBold = false;
    return `<p style="${S.p}">${html}</p>`;
  },
  strong(token) {
    const inner = this.parser.parseInline(token.tokens);
    // 判定规则：句子里有数字就留粗（数字才是证据）；整段只有一处加粗也留（收尾金句）。
    const keep = this._keepBold || this._forceBold || /\d/.test(token.text);
    return keep ? `<strong style="${S.strong}">${inner}</strong>` : inner;
  },
  em(token) {
    return `<em style="${S.em}">${this.parser.parseInline(token.tokens)}</em>`;
  },
  codespan(token) {
    return `<code style="${S.code}">${escapeHtml(token.text)}</code>`;
  },
  link(token) {
    // 公众号正文不放外链，只留文字。
    return this.parser.parseInline(token.tokens);
  },
  blockquote(token) {
    const plain = squash(token.text);
    const hero = HERO_QUOTES.some((k) => plain.includes(squash(k)));
    const paras = token.tokens
      .map((t) => {
        if (t.type !== 'paragraph') return this.parser.parse([t]);
        this._keepBold = true;
        const html = this.parser.parseInline(t.tokens);
        this._keepBold = false;
        return `<p style="${hero ? S.quoteCardP : S.quotePlainP}">${html}</p>`;
      })
      .join('');
    return hero ? `<blockquote style="${S.quoteCard}">${paras}</blockquote>` : paras;
  },
  list(token) {
    const items = token.items
      .map((item) => {
        const body = item.tokens
          .map((t) => (t.type === 'text' ? this.parser.parseInline(t.tokens) : this.parser.parse([t])))
          .join('');
        return `<li style="${S.li}">${body}</li>`;
      })
      .join('');
    const tag = token.ordered ? 'ol' : 'ul';
    return `<${tag} style="${token.ordered ? S.ol : S.ul}">${items}</${tag}>`;
  },
  table(token) {
    const head = token.header.map((c) => c.text).join('|');
    if (head.includes('一天里的活儿')) return renderCard('cards-day.md');
    if (head.includes('公司')) return renderCard('cards-companies.md');
    return `<p style="${S.p}">[表格]</p>`;
  },
  hr() {
    return `<hr style="${S.hr}">`;
  },
});

function renderCard(name) {
  const md = fs.readFileSync(path.join(WECHAT_DIR, name), 'utf8');
  renderer._forceBold = true;
  const html = marked.parse(md, { renderer, gfm: true, breaks: false });
  renderer._forceBold = false;
  return `<section style="${S.card}">${html}</section>`;
}

function markdownToWechatHtml(md) {
  return marked.parse(preprocess(stripFrontmatter(md)), { renderer, gfm: true, breaks: false }).trim();
}

// ---------------------------------------------------------------- 凭据与接口

function loadCredentials() {
  const envId = process.env.WECHAT_APP_ID;
  const envSecret = process.env.WECHAT_APP_SECRET;
  if (envId && envSecret) return { appid: envId, appsecret: envSecret };
  if (fs.existsSync(CRED_FILE)) {
    const raw = JSON.parse(fs.readFileSync(CRED_FILE, 'utf8'));
    if (raw.appid && raw.appsecret) return raw;
  }
  throw new Error(
    `找不到凭据。请创建 ${CRED_FILE}（内容 {"appid":"...","appsecret":"..."}）` +
      `，或设置环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET。`,
  );
}

function explainWxError(code, msg) {
  const map = {
    40001: 'AppSecret 不正确（密钥填错或已重置）',
    40002: 'grant_type 不合法',
    40013: 'AppID 不合法（公众号后台「基本配置」里复制）',
    40164: '调用来源 IP 不在白名单：请把本机公网 IP 加到「设置与开发 → 基本配置 → IP 白名单」',
    48001: '接口权限不足：未认证订阅号可能只能用群发接口，或改用「素材管理」+群发',
    41002: '缺少 access_token 参数',
    45009: '接口调用超过限制',
  };
  return `${msg || '未知错误'}（errcode ${code}）${map[code] ? ` —— ${map[code]}` : ''}`;
}

async function getAccessToken(creds) {
  if (fs.existsSync(TOKEN_CACHE)) {
    try {
      const cached = JSON.parse(fs.readFileSync(TOKEN_CACHE, 'utf8'));
      if (cached.access_token && cached.expires_at - 60 > Date.now()) {
        console.log(`· 复用缓存 access_token（还剩 ${Math.round((cached.expires_at - Date.now()) / 1000)}s）`);
        return cached.access_token;
      }
    } catch {
      /* 缓存坏了就重新取 */
    }
  }
  const url =
    `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential` +
    `&appid=${encodeURIComponent(creds.appid)}&secret=${encodeURIComponent(creds.appsecret)}`;
  const res = await fetch(url);
  const data = await res.json();
  if (data.errcode) throw new Error(explainWxError(data.errcode, data.errmsg));
  fs.mkdirSync(path.dirname(TOKEN_CACHE), { recursive: true });
  fs.writeFileSync(
    TOKEN_CACHE,
    JSON.stringify({ access_token: data.access_token, expires_at: Date.now() + data.expires_in * 1000 }),
  );
  console.log(`· 已获取 access_token（有效期 ${data.expires_in}s）`);
  return data.access_token;
}

/** 封面缩略图：JPG/PNG ≤ 64KB，超了接口会拒。 */
async function buildThumb(svgPath, outPath) {
  let quality = 90;
  for (; quality >= 30; quality -= 6) {
    const buf = await sharp(svgPath, { density: 384 })
      .resize(900, 900, { fit: 'cover' })
      .jpeg({ quality, chromaSubsampling: '4:2:0' })
      .toBuffer();
    if (buf.length <= 64 * 1024) {
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, buf);
      console.log(`· 封面缩略图 ${(buf.length / 1024).toFixed(1)}KB / ${quality}q → ${path.relative(ROOT, outPath)}`);
      return buf;
    }
  }
  throw new Error('封面压不到 64KB 以内，请换一张更简单的封面');
}

async function uploadThumb(token, buf) {
  const form = new FormData();
  form.append('media', new Blob([buf], { type: 'image/jpeg' }), 'thumb.jpg');
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${encodeURIComponent(token)}&type=thumb`,
    { method: 'POST', body: form },
  );
  const data = await res.json();
  if (data.errcode) throw new Error(explainWxError(data.errcode, data.errmsg));
  console.log(`· 封面已上传 media_id=${data.media_id}`);
  return data.media_id;
}

async function createDraft(token, article) {
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${encodeURIComponent(token)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        articles: [
          {
            title: article.title,
            author: article.author,
            digest: article.digest,
            content: article.content,
            content_source_url: article.sourceUrl,
            thumb_media_id: article.thumbMediaId,
            need_open_comment: 0,
            only_fans_can_comment: 0,
            pic_crop_235_1: '0_0_1_1',
            pic_crop_1_1: '0_0_1_1',
          },
        ],
      }),
    },
  );
  const data = await res.json();
  if (data.errcode) throw new Error(explainWxError(data.errcode, data.errmsg));
  return data;
}

// ---------------------------------------------------------------- 主流程

function parseArgs(argv) {
  const out = { publish: false, check: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--publish') out.publish = true;
    else if (a === '--check') out.check = true;
    else if (a.startsWith('--')) out[a.slice(2)] = argv[++i];
  }
  return out;
}

const DIGEST =
  '狼来了这次算不算数？2026 年几家大厂同时在做三件事：把 AI 写进研发流程、把经验做成 Agent 能读懂的规则、把「前端/后端」这个岗位分类从组织架构上抹掉。本文用一手材料拆开前端岗位的三个转折点：活儿被谁接走、谁来验收、经验归谁。';

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const srcPath = path.resolve(ROOT, args.src || DEFAULTS.src);
  const md = fs.readFileSync(srcPath, 'utf8');
  const fm = parseFrontmatter(md);

  if (args.check) {
    const creds = loadCredentials();
    console.log(`· AppID = ${creds.appid}`);
    await getAccessToken(creds);
    console.log('✓ 凭据与 access_token 正常。接下来可以跑 --publish。');
    return;
  }

  const html = markdownToWechatHtml(md);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, 'content.html'), html);

  const preview = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(fm.title || '微信草稿预览')}</title>
<style>
 body{margin:0;background:#ededed;font-family:-apple-system,"PingFang SC","WenQuanYi Micro Hei",sans-serif}
 .phone{max-width:414px;margin:0 auto;background:#fff;padding:18px 16px 40px}
 .bar{max-width:414px;margin:0 auto;padding:10px 16px;background:#07c160;color:#fff;font-size:13px}
 h1{font-size:20px;line-height:1.5;color:#1a1a1a;margin:0 0 6px}
 .meta{font-size:13px;color:#888;margin:0 0 18px;padding-bottom:14px;border-bottom:1px solid #eee}
 blockquote{margin:22px 0}
 p,li{word-break:break-word}
</style></head>
<body>
<div class="bar">草稿预览（仅本机）· 公众号后台会按自己的排版规则渲染</div>
<div class="phone">
<h1>${escapeHtml(fm.title || '')}</h1>
<p class="meta">huihao · ${escapeHtml(args.sourceUrl || DEFAULTS.sourceUrl)}</p>
${html}
</div></body></html>`;
  fs.writeFileSync(path.join(OUT_DIR, 'preview.html'), preview);

  console.log(`✓ 正文已生成：${path.relative(ROOT, path.join(OUT_DIR, 'content.html'))}`);
  console.log(`✓ 预览页面：${path.relative(ROOT, path.join(OUT_DIR, 'preview.html'))}`);
  const textLen = squash(html.replace(/<[^>]+>/g, '')).length;
  console.log(`· 标题 ${(fm.title || '').length} 字 · 正文 ${textLen} 字（上限 ${CONTENT_LIMIT} 字）`);
  console.log(`· HTML 体积 ${(html.length / 1024).toFixed(1)}KB（含 inline style）`);
  if (textLen > CONTENT_LIMIT) {
    console.warn(
      `⚠ 正文 ${textLen} 字，超过公众号 ${CONTENT_LIMIT} 字上限，` +
        `接口会拒；需要精简（常见做法：把「资料卡」整节移出正文，指到阅读原文）。`,
    );
  }

  if (!args.publish) {
    console.log('\n（未加 --publish，本地不联网。想写进公众号草稿箱就加 --publish）');
    return;
  }

  const creds = loadCredentials();
  const token = await getAccessToken(creds);
  const thumbBuf = await buildThumb(
    path.resolve(ROOT, args.thumb || DEFAULTS.thumb),
    path.join(OUT_DIR, 'thumb.jpg'),
  );
  const thumbMediaId = await uploadThumb(token, thumbBuf);
  const draft = await createDraft(token, {
    title: fm.title || args.title || '未命名',
    author: args.author || '',
    digest: args.digest || DIGEST,
    content: html,
    sourceUrl: args.sourceUrl || DEFAULTS.sourceUrl,
    thumbMediaId,
  });
  console.log(`✓ 已写入草稿箱 media_id=${draft.media_id}`);
  console.log('  去公众号后台「内容与互动 → 草稿箱」预览并点发布。');
}

main().catch((err) => {
  console.error(`✗ ${err.message}`);
  process.exit(1);
});
