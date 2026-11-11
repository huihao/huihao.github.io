/**
 * Build the icon set of the site: the app icons, the social card and the
 * favicon.
 *
 * The sources are the SVG files in src/img, sharp turns them into the PNGs the
 * browsers and the platforms ask for, and the favicon.ico is assembled from
 * the PNGs by hand (an .ico file is a small container that may hold PNG data).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = path.join(root, 'src', 'img');
const outDir = path.join(root, 'dist', 'img');

/** Render an SVG source into a PNG of the given size. */
async function render(source, size, target) {
    const buffer = await sharp(source, { density: 384 })
        .resize(size, size, { fit: 'cover' })
        .png({ compressionLevel: 9 })
        .toBuffer();

    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, buffer);

    return buffer;
}

/** Render an SVG source into a PNG of an exact size (no cropping). */
async function renderExact(source, width, height, target) {
    const buffer = await sharp(source, { density: 384 })
        .resize(width, height, { fit: 'fill' })
        .png({ compressionLevel: 9 })
        .toBuffer();

    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, buffer);

    return buffer;
}

/** Assemble PNG images into an .ico container. */
function buildIco(images) {
    const header = Buffer.alloc(6);
    header.writeUInt16LE(0, 0);
    header.writeUInt16LE(1, 2);
    header.writeUInt16LE(images.length, 4);

    const entries = [];
    let offset = 6 + images.length * 16;

    for (const image of images) {
        const entry = Buffer.alloc(16);
        entry.writeUInt8(image.size >= 256 ? 0 : image.size, 0);
        entry.writeUInt8(image.size >= 256 ? 0 : image.size, 1);
        entry.writeUInt8(0, 2);
        entry.writeUInt8(0, 3);
        entry.writeUInt16LE(1, 4);
        entry.writeUInt16LE(32, 6);
        entry.writeUInt32LE(image.data.length, 8);
        entry.writeUInt32LE(offset, 12);
        entries.push(entry);
        offset += image.data.length;
    }

    return Buffer.concat([header, ...entries, ...images.map((image) => image.data)]);
}

async function build() {
    const appIcon = path.join(srcDir, 'app-icon.svg');
    const favicon = path.join(srcDir, 'favicon.svg');
    const social = path.join(srcDir, 'og-default.svg');

    // The app icons: iOS masks them into its own shape, so they are full bleed.
    for (const size of [180, 192, 512]) {
        const name = size === 180 ? 'apple-touch-icon.png' : `icon-${size}.png`;
        await render(appIcon, size, path.join(outDir, name));
        console.log(`icon dist/img/${name} (${size}x${size})`);
    }

    // The social card used when a page has no picture of its own.
    await renderExact(social, 1200, 630, path.join(outDir, 'og-default.png'));
    console.log('icon dist/img/og-default.png (1200x630)');

    // The favicon: an .ico for the old browsers, an SVG for the modern ones.
    const sizes = [16, 32, 48];
    const images = [];

    for (const size of sizes) {
        images.push({ size, data: await render(favicon, size, path.join(outDir, `.favicon-${size}.png`)) });
    }

    await fs.writeFile(path.join(root, 'favicon.ico'), buildIco(images));
    console.log(`icon favicon.ico (${sizes.join('/')})`);

    for (const size of sizes) {
        await fs.rm(path.join(outDir, `.favicon-${size}.png`), { force: true });
    }

    await fs.copyFile(favicon, path.join(root, 'favicon.svg'));
    console.log('icon favicon.svg');

    // The cover images of the posts that ship with the repository: an SVG
    // source is rendered into the 570x144 banner the cards use.
    const sources = await fs.readdir(srcDir);
    const covers = sources.filter((file) => file.startsWith('cover-') && file.endsWith('.svg'));

    for (const file of covers) {
        const name = file.replace(/\.svg$/, '.png');
        await renderExact(path.join(srcDir, file), 570, 144, path.join(outDir, name));
        console.log(`icon dist/img/${name} (570x144)`);
    }
}

await build();
