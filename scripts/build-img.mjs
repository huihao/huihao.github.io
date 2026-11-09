/**
 * Copy the images in src/img into dist/img, compressing them on the way.
 *
 * Replaces the old `gulp-imagemin` task. sharp is used instead because the
 * imagemin plugins download their binaries from GitHub releases, which is not
 * reliable in every network environment; sharp ships its binaries through npm.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = path.join(root, 'src', 'img');
const outDir = path.join(root, 'dist', 'img');

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(full)));
    else files.push(full);
  }
  return files;
}

async function copy(file, target) {
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.copyFile(file, target);
}

/**
 * Re-encode an image and keep the result only when it is actually smaller than
 * the original. sharp cannot always beat the palette quantization that
 * pngquant did for the old build, and an image that grows is never worth it.
 */
async function optimize(file, target) {
  const ext = path.extname(file).toLowerCase();
  const original = await fs.readFile(file);

  await fs.mkdir(path.dirname(target), { recursive: true });

  let pipeline;
  if (ext === '.png') {
    pipeline = sharp(file).png({ compressionLevel: 9 });
  } else if (ext === '.jpg' || ext === '.jpeg') {
    pipeline = sharp(file).jpeg({ quality: 82, mozjpeg: true });
  } else {
    await copy(file, target);
    return { bytes: original.length, kept: 'copy' };
  }

  const optimized = await pipeline.toBuffer();
  if (optimized.length < original.length) {
    await fs.writeFile(target, optimized);
    return { bytes: optimized.length, kept: 'optimized' };
  }

  await fs.writeFile(target, original);
  return { bytes: original.length, kept: 'original' };
}

async function build() {
  let files;
  try {
    files = await walk(srcDir);
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.log('img  no src/img directory, nothing to do');
      return;
    }
    throw error;
  }

  let saved = 0;
  for (const file of files) {
    const target = path.join(outDir, path.relative(srcDir, file));

    try {
      const { bytes, kept } = await optimize(file, target);
      saved += (await fs.stat(file)).size - bytes;
      console.log(`img  ${path.relative(root, file)} -> ${kept} (${bytes} bytes)`);
    } catch (error) {
      console.warn(`img  ${path.relative(root, file)}: ${error.message}, copied as-is`);
      await copy(file, target);
    }
  }

  console.log(`img  ${files.length} file(s) -> ${path.relative(root, outDir)}`);
}

await build();
