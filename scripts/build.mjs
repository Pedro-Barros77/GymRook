import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const root = fileURLToPath(new URL('../dist/', import.meta.url));
const excluded = new Set(['sw.js', 'asset-manifest.json', '.nojekyll']);
const files = [];
async function walk(dir) {
  for (const item of await readdir(dir, { withFileTypes: true })) {
    const absolute = path.join(dir, item.name);
    if (item.isDirectory()) await walk(absolute);
    else {
      const relative = path.relative(root, absolute).split(path.sep).join('/');
      if (!excluded.has(relative)) files.push(relative);
    }
  }
}
await walk(root);
files.sort();
const hash = crypto.createHash('sha256');
const swPath = path.join(root, 'sw.js');
const sw = await readFile(swPath, 'utf8');
// Worker behavior is part of a release; normalize its embedded hash to avoid a cycle.
hash.update('sw.js').update(sw.replace(/const VERSION = '[^']+';/, "const VERSION = 'release';"));
let bytes = 0;
for (const file of files) {
  const body = await readFile(path.join(root, file));
  hash.update(file).update(body);
  bytes += body.length;
}
const version = hash.digest('hex').slice(0, 16);
await writeFile(path.join(root, 'asset-manifest.json'), JSON.stringify({ version, bytes, files: files.map(file => './' + file) }, null, 2) + '\n');
await writeFile(swPath, sw.replace(/const VERSION = '[^']+';/, `const VERSION = '${version}';`));
console.log(`Pronto: ${files.length} arquivos, ${(bytes / 1024 / 1024).toFixed(2)} MB, versão ${version}.`);
