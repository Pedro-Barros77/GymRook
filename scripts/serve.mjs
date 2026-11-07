import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('../dist', import.meta.url)));
const port = Number(process.env.PORT || 4173);
const host = process.env.GYMROOK_HOST || '127.0.0.1';
const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.json':'application/json', '.webmanifest':'application/manifest+json', '.svg':'image/svg+xml', '.png':'image/png', '.gif':'image/gif', '.webp':'image/webp', '.mp4':'video/mp4', '.ico':'image/x-icon' };

http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(root, '.' + pathname);
    if (file !== root && !file.startsWith(root + path.sep)) {
      res.writeHead(403).end('Forbidden');
      return;
    }
    const meta = await stat(file);
    const actual = meta.isDirectory() ? path.join(file, 'index.html') : file;
    const body = await readFile(actual);
    const headers = {
      'Content-Type': types[path.extname(actual)] || 'application/octet-stream',
      'Cache-Control': 'no-cache',
      'X-Content-Type-Options': 'nosniff',
      'Accept-Ranges': 'bytes',
      'Content-Length': body.length
    };
    if (req.headers.range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
      let start = match?.[1] ? Number(match[1]) : null;
      let end = match?.[2] ? Number(match[2]) : null;
      if (start === null && end !== null) { start = Math.max(0, body.length - end); end = body.length - 1; }
      else if (end === null) end = body.length - 1;
      if (!match || start === null || !Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start >= body.length || end < start) {
        res.writeHead(416, { 'Content-Range': `bytes */${body.length}` }).end();
        return;
      }
      end = Math.min(end, body.length - 1);
      res.writeHead(206, { ...headers, 'Content-Length': end - start + 1, 'Content-Range': `bytes ${start}-${end}/${body.length}` });
      res.end(req.method === 'HEAD' ? undefined : body.subarray(start, end + 1));
      return;
    }
    res.writeHead(200, headers);
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Arquivo não encontrado.');
  }
}).listen(port, host, () => console.log(`GymRook: http://${host}:${port}/`));
