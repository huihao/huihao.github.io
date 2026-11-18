/**
 * Render the two WeChat cover images from their SVG sources.
 *
 *   node drafts/ai-frontend-role-evolution/wechat/render-covers.mjs
 *
 * The SVG sources carry the Chinese title, so the renderer needs a CJK font on
 * the machine (fontconfig). Debian/Ubuntu: apt-get install fonts-wqy-microhei
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const here = path.dirname(fileURLToPath(import.meta.url));

const covers = [
    { file: 'cover-2.35-1', width: 900, height: 383, note: '头条封面 2.35:1' },
    { file: 'cover-1-1', width: 900, height: 900, note: '次条封面 1:1' }
];

for (const cover of covers) {
    const source = path.join(here, `${cover.file}.svg`);
    const target = path.join(here, `${cover.file}.png`);
    const buffer = await sharp(source, { density: 384 })
        .resize(cover.width, cover.height, { fit: 'fill' })
        .png({ compressionLevel: 9 })
        .toBuffer();

    await fs.writeFile(target, buffer);
    console.log(`${cover.file}.png  ${cover.width}x${cover.height}  ${(buffer.length / 1024).toFixed(1)}KB  (${cover.note})`);
}
