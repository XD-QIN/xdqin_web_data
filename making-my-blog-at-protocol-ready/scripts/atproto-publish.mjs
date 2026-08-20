/**
 * Publish this site's blog posts to the atmosphere as standard.site records.
 *
 *   npm run atproto:publish -- --dry-run          # prints, touches nothing
 *   ATP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx npm run atproto:publish
 *
 * What it writes to your repo (the AT Protocol one, not git):
 *   • one `site.standard.publication` record — the blog itself, at rkey `self`
 *   • one `site.standard.document` per published post
 * and back into *this* repo: the returned AT-URI, as `atUri` in each post's
 * frontmatter, which is what makes the <link rel="site.standard.document"> tag
 * appear on the page.
 *
 * Design notes, since the obvious alternatives are worse:
 *
 *   No dependencies. Everything here is `fetch` against three XRPC methods
 *   (createSession, uploadBlob, putRecord) plus a DID lookup. Adding a
 *   publishing CLI would mean trusting a third party with an app password on
 *   every run, for maybe 150 lines of work.
 *
 *   No state file. The record key is derived from the post — `tech-<slug>` —
 *   so a second run *updates* the same records instead of creating duplicates.
 *   Nothing to commit, nothing to lose, nothing to get out of sync with the
 *   posts themselves. Rename a post's file and you get a new record; that is
 *   correct, because its URL changed too.
 *
 *   No pointless writes. Each record is compared against what's already in the
 *   repo and skipped if identical, down to the cover image (whose blob CID is
 *   computed locally, so an unchanged cover isn't even re-uploaded). Every
 *   write is a signed commit that goes out over the firehose; re-running this
 *   after changing one post shouldn't republish the other two.
 *
 *   Metadata only, by default. The record carries title/description/date/tags
 *   and the path back to xdqin.com, so a reader app renders a card and the
 *   click lands here. `--full-text` additionally embeds the post's text in the
 *   record, which lets reader apps show the whole piece without ever visiting
 *   the site. That's a real trade (reach vs. traffic, and a permanently public,
 *   trivially-indexed copy), so it's opt-in — and reversible in one direction
 *   only, practically speaking: the copies are already out there.
 *
 * Runs from the Cloudflare build as well as by hand — see `build:deploy` in
 * package.json. There it publishes *before* Astro builds, so the `atUri` it
 * writes lands in the frontmatter that same build reads, and the page ships
 * with its <link> tag without anything being committed back to git. That
 * ordering is what keeps the tag proof-carrying: it exists in a deploy only
 * because putRecord succeeded seconds earlier in the same run. The value is
 * deterministic, so committing the write-back and not committing it converge
 * on the same bytes — either is fine.
 *
 * Flags:
 *   --dry-run      build and print the records; no network, no credentials
 *   --full-text    include the post body as `textContent`
 *   --drafts       include posts marked `draft: true` (they 404 in production)
 *   --section=tech|photography   publish just one blog
 *   --skip-if-unconfigured       exit 0 when no DID is set, instead of failing.
 *                  For the build pipeline: a site that hasn't opted in should
 *                  still deploy. Deliberately keyed on the DID *only* — once an
 *                  identity is configured, a missing password is a broken
 *                  deploy and should say so rather than quietly stop publishing.
 *   --production-branch=main     publish only from that branch, when the build
 *                  environment names one. Cloudflare builds non-production
 *                  branches too, and those must not publish: a branch's new
 *                  post would create a record pointing at a URL that 404s until
 *                  merge, and an edit would overwrite the live record before
 *                  anyone approved it. Only the branch that is actually served
 *                  gets to speak for the site.
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, extname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import config, { isDid, isAtUri } from '../atproto.config.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CONTENT = join(ROOT, 'src', 'content');

// Where the publication lives on the web. Must match `site` in astro.config.mjs:
// it is the base a document's `path` is appended to, and the origin whose
// /.well-known/site.standard.publication an indexer will come back to check.
const SITE_URL = 'https://xdqin.com';

// The two blogs, as one publication. standard.site models a publication as a
// single base URL plus per-document paths, and that is honest to how the site
// reads — one person writing about two things, not two magazines. `dir` is the
// content folder, `prefix` the URL segment it's served under.
const SECTIONS = [
  { dir: 'tech', prefix: '/blog/tech' },
  { dir: 'photography', prefix: '/blog/photography' },
];

// Square, ≥256px, and already the site's mark.
const PUBLICATION_ICON = join(ROOT, 'public', 'favicon.png');

const PUBLICATION_COLLECTION = 'site.standard.publication';
const DOCUMENT_COLLECTION = 'site.standard.document';
const PUBLICATION_RKEY = 'self';

// Stand-in identity so --dry-run works with an empty config — the point of a
// dry run is to eyeball paths and titles *before* there's an account.
const PLACEHOLDER_DID = 'did:plc:aaaaaaaaaaaaaaaaaaaaaaaa';

// ── Arguments ───────────────────────────────────────────────────────────────

const argv = process.argv.slice(2);
const has = (flag) => argv.includes(flag);
const valueOf = (name) => {
  const hit = argv.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};
const DRY_RUN = has('--dry-run');
const FULL_TEXT = has('--full-text');
const INCLUDE_DRAFTS = has('--drafts');
const SKIP_IF_UNCONFIGURED = has('--skip-if-unconfigured');
const ONLY_SECTION = valueOf('section');
const PRODUCTION_BRANCH = valueOf('production-branch');

const unknown = argv.filter(
  (a) =>
    !['--dry-run', '--full-text', '--drafts', '--skip-if-unconfigured'].includes(a) &&
    !a.startsWith('--section=') &&
    !a.startsWith('--production-branch=')
);
if (unknown.length) die(`Unknown argument(s): ${unknown.join(' ')}`);
if (ONLY_SECTION && !SECTIONS.some((s) => s.dir === ONLY_SECTION)) {
  die(`--section must be one of: ${SECTIONS.map((s) => s.dir).join(', ')}`);
}

function die(message) {
  console.error(`\n  ✗ ${message}\n`);
  process.exit(1);
}

// ── Frontmatter ─────────────────────────────────────────────────────────────
//
// A deliberately small YAML reader: exactly the shapes README documents for a
// post, and a loud error on anything else. It would be easy to make this
// forgiving, and that would be the wrong call — a value this misreads becomes a
// signed, published claim about a post, so "I don't understand line 7" has to
// beat a plausible guess.

function unquote(raw, where) {
  const value = raw.trim();
  if (value.startsWith("'")) {
    if (!value.endsWith("'") || value.length < 2) die(`${where}: unterminated ' quote`);
    return value.slice(1, -1).replace(/''/g, "'"); // YAML escapes ' as ''
  }
  if (value.startsWith('"')) {
    if (!value.endsWith('"') || value.length < 2) die(`${where}: unterminated " quote`);
    return value.slice(1, -1).replace(/\\(["\\])/g, '$1');
  }
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (value.startsWith('|') || value.startsWith('>')) {
    die(`${where}: block scalars (| and >) aren't supported — keep the value on one line`);
  }
  return value;
}

function parseFrontmatter(source, where) {
  const lines = source.split(/\r?\n/);
  if (lines[0] !== '---') die(`${where}: file must start with a '---' frontmatter block`);
  const end = lines.indexOf('---', 1);
  if (end === -1) die(`${where}: frontmatter block is never closed`);

  const data = {};
  let currentKey = null; // set while reading a "- item" block sequence
  for (let i = 1; i < end; i++) {
    const line = lines[i];
    const at = `${where}:${i + 1}`;
    if (!line.trim() || line.trim().startsWith('#')) continue;

    const item = /^\s+-\s+(.*)$/.exec(line);
    if (item) {
      if (!currentKey || !Array.isArray(data[currentKey])) die(`${at}: unexpected list item`);
      data[currentKey].push(unquote(item[1], at));
      continue;
    }

    const pair = /^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$/.exec(line);
    if (!pair) die(`${at}: can't read this frontmatter line — ${JSON.stringify(line)}`);
    const [, key, rest] = pair;
    currentKey = key;

    if (rest === '') {
      data[key] = []; // a block sequence follows (or an empty value)
    } else if (rest.startsWith('[')) {
      if (!rest.trim().endsWith(']')) die(`${at}: keep a [flow, list] on one line`);
      const inner = rest.trim().slice(1, -1).trim();
      data[key] = inner ? splitFlow(inner, at).map((v) => unquote(v, at)) : [];
    } else {
      data[key] = unquote(rest, at);
    }
  }

  return { data, body: lines.slice(end + 1).join('\n').trim() };
}

// Split "a, 'b, c', d" on the commas that are actually separators.
function splitFlow(inner, where) {
  const out = [];
  let buf = '';
  let quote = null;
  for (const ch of inner) {
    if (quote) {
      if (ch === quote) quote = null;
      buf += ch;
    } else if (ch === "'" || ch === '"') {
      quote = ch;
      buf += ch;
    } else if (ch === ',') {
      out.push(buf);
      buf = '';
    } else {
      buf += ch;
    }
  }
  if (quote) die(`${where}: unterminated quote in list`);
  if (buf.trim()) out.push(buf);
  return out;
}

// Write `atUri` back into a post's frontmatter, replacing any existing value.
async function writeAtUri(file, uri) {
  const source = await readFile(file, 'utf8');
  const lines = source.split(/\r?\n/);
  const end = lines.indexOf('---', 1);
  const existing = lines.findIndex((l, i) => i > 0 && i < end && /^atUri:\s/.test(l));
  const entry = `atUri: '${uri}'`;
  if (existing !== -1) lines[existing] = entry;
  else lines.splice(end, 0, entry);
  await writeFile(file, lines.join('\n'), 'utf8');
}

// ── Posts ───────────────────────────────────────────────────────────────────

async function collectPosts() {
  const posts = [];
  for (const section of SECTIONS) {
    if (ONLY_SECTION && section.dir !== ONLY_SECTION) continue;
    const base = join(CONTENT, section.dir);
    for (const file of await walk(base)) {
      if (!/\.mdx?$/.test(file)) continue;
      const where = relative(ROOT, file);
      const { data, body } = parseFrontmatter(await readFile(file, 'utf8'), where);

      if (data.draft === true && !INCLUDE_DRAFTS) continue;
      for (const required of ['title', 'description', 'pubDate']) {
        if (!data[required]) die(`${where}: missing required frontmatter '${required}'`);
      }

      // Astro's glob loader ids a post by its path under the collection base,
      // minus the extension — that id is the URL slug, so derive it the same way.
      const slug = relative(base, file).split(sep).join('/').replace(/\.mdx?$/, '');

      // A date-only `pubDate` carries no time, and midnight UTC is the wrong
      // instant to fill in: reader apps format `publishedAt` in the viewer's
      // timezone, so anyone west of UTC sees the *previous* day — the card
      // under a shared link then disagrees with the date printed on the page it
      // links to. Noon UTC is the same calendar day from UTC-12 to UTC+11,
      // which is everywhere that isn't the far side of the date line. A
      // frontmatter value that does specify a time is honoured exactly.
      const raw = String(data.pubDate).trim();
      const publishedAt = new Date(
        /^\d{4}-\d{2}-\d{2}$/.test(raw) ? `${raw}T12:00:00.000Z` : raw
      );
      if (Number.isNaN(publishedAt.getTime())) die(`${where}: pubDate isn't a date`);

      posts.push({
        file,
        where,
        section,
        slug,
        // The trailing slash is not optional: `trailingSlash: 'always'` means
        // /blog/tech/<slug>/ is the page and /blog/tech/<slug> is a 301 to it.
        // Verification compares this against the live URL, so the slashless
        // form would invalidate the record.
        path: `${section.prefix}/${slug}/`,
        title: String(data.title),
        description: String(data.description),
        tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
        cover: data.cover ? resolve(dirname(file), String(data.cover)) : null,
        atUri: typeof data.atUri === 'string' ? data.atUri : null,
        publishedAt,
        body,
      });
    }
  }
  posts.sort((a, b) => b.publishedAt - a.publishedAt);
  return posts;
}

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(full)));
    else out.push(full);
  }
  return out;
}

// A record key has to survive `[A-Za-z0-9._~-]`, and the section prefix keeps
// the two blogs from ever colliding on a shared slug.
function documentRkey(post) {
  const key = `${post.section.dir}-${post.slug}`.replace(/[^A-Za-z0-9._~-]/g, '-');
  if (key.length > 512) die(`${post.where}: slug is too long for a record key`);
  return key;
}

// Markdown → the plain text a reader app would show. Not a full renderer: it
// drops the syntax that carries no meaning read aloud, and leaves the words.
function plainText(markdown) {
  return markdown
    .replace(/^import\s+.*$/gm, '') // MDX component imports
    .replace(/<[A-Z][^>]*\/>/g, '') // <Photo … />, <Gallery … />
    .replace(/^```.*$/gm, '') // fence markers, keeping the code between them
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '') // images
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // links → their text
    .replace(/^#{1,6}\s+/gm, '') // heading hashes
    .replace(/^\s*>\s?/gm, '') // block quotes
    .replace(/(\*\*|__|\*|_|`)/g, '') // emphasis + inline code marks
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ── Blobs ───────────────────────────────────────────────────────────────────

const MIME = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.gif': 'image/gif',
};

const BASE32 = 'abcdefghijklmnopqrstuvwxyz234567';

function base32(bytes) {
  let bits = 0;
  let value = 0;
  let out = '';
  for (const byte of bytes) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      out += BASE32[(value >>> bits) & 31];
      // Drop the bits just emitted: without this the accumulator keeps every
      // byte ever seen and overflows 32 bits a few bytes in, silently
      // corrupting the CID.
      value &= (1 << bits) - 1;
    }
  }
  if (bits > 0) out += BASE32[(value << (5 - bits)) & 31];
  return out;
}

// The CID a PDS will give these bytes: CIDv1, raw codec (0x55), sha2-256
// (0x12 0x20), base32-lower with the 'b' multibase prefix. Computing it here is
// what lets an unchanged cover image be recognised without re-uploading it.
function blobCid(bytes) {
  const digest = createHash('sha256').update(bytes).digest();
  return 'b' + base32(Uint8Array.from([0x01, 0x55, 0x12, 0x20, ...digest]));
}

// ── XRPC ────────────────────────────────────────────────────────────────────

async function xrpc(pds, method, { body, headers = {}, token, query } = {}) {
  const url = new URL(`/xrpc/${method}`, pds);
  if (query) for (const [k, v] of Object.entries(query)) url.searchParams.set(k, v);
  const init = { method: body === undefined ? 'GET' : 'POST', headers: { ...headers } };
  if (token) init.headers.authorization = `Bearer ${token}`;
  if (body !== undefined) {
    if (body instanceof Uint8Array) init.body = body;
    else {
      init.headers['content-type'] = 'application/json';
      init.body = JSON.stringify(body);
    }
  }
  const res = await fetch(url, init);
  const text = await res.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    /* non-JSON error page */
  }
  if (!res.ok) {
    const err = payload?.error ? `${payload.error}: ${payload.message ?? ''}` : text.slice(0, 300);
    const error = new Error(`${method} → ${res.status} ${err.trim()}`);
    error.xrpc = payload?.error ?? null;
    throw error;
  }
  return payload;
}

// Find the account's PDS from its DID document rather than assuming
// bsky.social, so a self-hosted or migrated account works untouched.
async function resolvePds(did) {
  if (process.env.ATP_SERVICE) return process.env.ATP_SERVICE.replace(/\/+$/, '');
  let doc;
  if (did.startsWith('did:plc:')) {
    const res = await fetch(`https://plc.directory/${did}`);
    if (!res.ok) die(`Couldn't resolve ${did} at plc.directory (HTTP ${res.status})`);
    doc = await res.json();
  } else if (did.startsWith('did:web:')) {
    // did:web:example.com          → https://example.com/.well-known/did.json
    // did:web:example.com:u:alice  → https://example.com/u/alice/did.json
    // Split on ':' before decoding, so a percent-encoded port stays in the host.
    const [host, ...path] = did.slice('did:web:'.length).split(':').map(decodeURIComponent);
    const url = path.length
      ? `https://${host}/${path.join('/')}/did.json`
      : `https://${host}/.well-known/did.json`;
    const res = await fetch(url);
    if (!res.ok) die(`Couldn't fetch ${url} (HTTP ${res.status})`);
    doc = await res.json();
  } else {
    die(`Unsupported DID method in ${did} — set ATP_SERVICE to your PDS URL`);
  }
  const service = (doc.service ?? []).find((s) => String(s.id).endsWith('#atproto_pds'));
  if (!service?.serviceEndpoint) die(`${did}'s DID document lists no #atproto_pds service`);
  return String(service.serviceEndpoint).replace(/\/+$/, '');
}

async function getRecord(pds, did, collection, rkey) {
  try {
    const res = await xrpc(pds, 'com.atproto.repo.getRecord', {
      query: { repo: did, collection, rkey },
    });
    return res?.value ?? null;
  } catch (err) {
    if (err.xrpc === 'RecordNotFound') return null;
    throw err;
  }
}

// ── Records ─────────────────────────────────────────────────────────────────

const prune = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined));

function publicationRecord(icon) {
  const { name, description } = config.publication ?? {};
  if (!name) die('atproto.config.js: publication.name is required.');
  return prune({
    $type: PUBLICATION_COLLECTION,
    url: SITE_URL,
    name,
    description: description || undefined,
    icon,
  });
}

function documentRecord(post, publicationUri, coverImage) {
  return prune({
    $type: DOCUMENT_COLLECTION,
    site: publicationUri,
    path: post.path,
    title: post.title,
    description: post.description,
    publishedAt: post.publishedAt.toISOString(),
    tags: post.tags.length ? post.tags : undefined,
    coverImage,
    textContent: FULL_TEXT ? plainText(post.body) : undefined,
  });
}

// Compare what we'd write against what's there, so an unchanged post isn't
// re-signed and re-broadcast. Key order is normalised; blob refs compare by CID.
const same = (a, b) => stable(a) === stable(b);
const stable = (value) => {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${stable(value[k])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
};

/**
 * The blob ref for an image, without re-uploading bytes the repo already has.
 * `existing` is whatever blob the current record points at; if its CID matches
 * these bytes, it is reused verbatim.
 */
async function blobFor(session, file, existing) {
  let bytes;
  try {
    bytes = new Uint8Array(await readFile(file));
  } catch {
    console.warn(`    ! cover image not found: ${relative(ROOT, file)} — publishing without it`);
    return undefined;
  }
  const mimeType = MIME[extname(file).toLowerCase()];
  if (!mimeType) {
    console.warn(`    ! unsupported cover type: ${relative(ROOT, file)} — publishing without it`);
    return undefined;
  }
  const cid = blobCid(bytes);
  if (existing?.ref?.$link === cid) return existing;
  if (!session) return { $type: 'blob', ref: { $link: cid }, mimeType, size: bytes.length };

  try {
    const res = await xrpc(session.pds, 'com.atproto.repo.uploadBlob', {
      body: bytes,
      headers: { 'content-type': mimeType },
      token: session.token,
    });
    return res.blob;
  } catch (err) {
    // A cover is worth having but never worth failing the post over — an
    // oversized image or a PDS blob limit shouldn't block the text.
    console.warn(`    ! couldn't upload ${relative(ROOT, file)} (${err.message}) — skipping cover`);
    return undefined;
  }
}

// ── Run ─────────────────────────────────────────────────────────────────────

// Which branch this build is for, as the CI that's running us names it. A local
// run sets none of these, and that's the signal for "manual run, go ahead".
const CI_BRANCH_VARS = ['WORKERS_CI_BRANCH', 'CF_PAGES_BRANCH', 'GITHUB_REF_NAME'];

/**
 * True when this run should stop because it isn't the branch that serves the
 * site. Prints what it detected either way: if the build environment ever
 * renames its branch variable, the log says "no CI branch detected" on a branch
 * build, which is the one place you'd notice the guard had stopped engaging.
 */
function wrongBranch() {
  if (!PRODUCTION_BRANCH) return false;
  const found = CI_BRANCH_VARS.map((v) => [v, process.env[v]]).find(([, value]) => value);
  if (!found) {
    console.log('\n  No CI branch detected — treating this as a manual run.');
    return false;
  }
  const [name, branch] = found;
  if (branch === PRODUCTION_BRANCH) return false;
  console.log(
    `\n  ${name}=${branch} is not the production branch (${PRODUCTION_BRANCH}) —\n` +
      '  skipping standard.site publishing. Only the branch that actually serves\n' +
      "  the site may speak for it; a branch's records would point at URLs that\n" +
      '  404 until merge.\n'
  );
  return true;
}

async function main() {
  if (wrongBranch()) return;

  const did = isDid(config.did) ? config.did : DRY_RUN ? PLACEHOLDER_DID : null;
  if (!did) {
    if (SKIP_IF_UNCONFIGURED) {
      console.log('\n  No DID in atproto.config.js — skipping standard.site publishing.\n');
      return;
    }
    die(
      'No DID configured. Put yours in atproto.config.js (see the setup steps there),\n' +
        '    or run with --dry-run to preview the records without an account.'
    );
  }

  const posts = await collectPosts();
  if (!posts.length) die('No published posts found — nothing to publish.');

  let session = null;
  if (!DRY_RUN) {
    const identifier = process.env.ATP_IDENTIFIER || config.handle;
    const password = process.env.ATP_APP_PASSWORD;
    if (!identifier) die('Set `handle` in atproto.config.js, or pass ATP_IDENTIFIER.');
    if (!password) {
      die(
        'ATP_APP_PASSWORD is not set. Create an app password (Settings → Privacy and\n' +
          '    security → App passwords) and pass it in the environment — never your\n' +
          '    account password, and never commit it.'
      );
    }
    const pds = await resolvePds(did);
    const auth = await xrpc(pds, 'com.atproto.server.createSession', {
      body: { identifier, password },
    });
    // Guards against publishing into the wrong repo if the config and the
    // credentials have drifted apart.
    if (auth.did !== did) {
      die(`Signed in as ${auth.did}, but atproto.config.js says ${did}. Refusing to publish.`);
    }
    session = { pds, token: auth.accessJwt, did: auth.did };
    console.log(`\n  Signed in as ${auth.handle} (${auth.did})\n  PDS: ${pds}`);
  } else {
    console.log('\n  Dry run — nothing will be published.');
    if (!isDid(config.did)) console.log(`  (No DID configured; showing ${PLACEHOLDER_DID}.)`);
  }

  // ── Publication ──
  const configuredPublication = isAtUri(config.publicationUri) ? config.publicationUri : null;
  const publicationRkey = configuredPublication
    ? configuredPublication.split('/').pop()
    : PUBLICATION_RKEY;
  const publicationUri = `at://${did}/${PUBLICATION_COLLECTION}/${publicationRkey}`;

  const currentPublication = session
    ? await getRecord(session.pds, did, PUBLICATION_COLLECTION, publicationRkey)
    : null;
  const icon = await blobFor(session, PUBLICATION_ICON, currentPublication?.icon);
  const publication = publicationRecord(icon);

  console.log(`\n  ${PUBLICATION_COLLECTION}/${publicationRkey}`);
  if (DRY_RUN) {
    console.log(indent(publication));
  } else if (same(publication, currentPublication)) {
    console.log('    unchanged');
  } else {
    await xrpc(session.pds, 'com.atproto.repo.putRecord', {
      body: {
        repo: did,
        collection: PUBLICATION_COLLECTION,
        rkey: publicationRkey,
        record: publication,
      },
      token: session.token,
    });
    console.log(`    ${currentPublication ? 'updated' : 'created'} → ${publicationUri}`);
  }

  // ── Documents ──
  let written = 0;
  for (const post of posts) {
    const rkey = documentRkey(post);
    const uri = `at://${did}/${DOCUMENT_COLLECTION}/${rkey}`;
    const current = session
      ? await getRecord(session.pds, did, DOCUMENT_COLLECTION, rkey)
      : null;
    const coverImage = post.cover
      ? await blobFor(session, post.cover, current?.coverImage)
      : undefined;
    const record = documentRecord(post, publicationUri, coverImage);

    console.log(`\n  ${DOCUMENT_COLLECTION}/${rkey}`);
    console.log(`    ${SITE_URL}${post.path}`);
    if (DRY_RUN) {
      console.log(indent(record));
      continue;
    }

    const bytes = Buffer.byteLength(JSON.stringify(record));
    if (bytes > 500_000) {
      console.warn(`    ! record is ${Math.round(bytes / 1000)} kB — large enough that the PDS may reject it`);
    }

    if (same(record, current)) {
      console.log('    unchanged');
    } else {
      await xrpc(session.pds, 'com.atproto.repo.putRecord', {
        body: { repo: did, collection: DOCUMENT_COLLECTION, rkey, record },
        token: session.token,
      });
      console.log(`    ${current ? 'updated' : 'created'} → ${uri}`);
      written++;
    }

    if (post.atUri !== uri) {
      await writeAtUri(post.file, uri);
      console.log(`    wrote atUri into ${post.where}`);
    }
  }

  // ── What's left for a human ──
  console.log('');
  if (DRY_RUN) {
    console.log(
      '  Check the paths above against the live URLs — they must match exactly,\n' +
        '  trailing slash included, or verification fails.\n'
    );
    return;
  }

  console.log(`  Done — ${written} record${written === 1 ? '' : 's'} written.\n`);
  if (!configuredPublication) {
    console.log('  One step left. Put this in atproto.config.js as `publicationUri`:\n');
    console.log(`      publicationUri: '${publicationUri}',\n`);
    console.log(
      '  then commit and deploy, so /.well-known/site.standard.publication starts\n' +
        '  answering with it. Until then the records exist but nothing verifies.\n'
    );
  } else {
    console.log('  Commit the frontmatter changes and deploy, so each post carries its\n  <link rel="site.standard.document"> tag.\n');
  }
}

const indent = (obj) =>
  JSON.stringify(obj, null, 2)
    .split('\n')
    .map((l) => `    ${l}`)
    .join('\n');

main().catch((err) => die(err.stack || err.message));
