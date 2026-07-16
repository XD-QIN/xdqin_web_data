/**
 * First-party, privacy-friendly page-view counter (Cloudflare Worker + D1).
 *
 * The site is still a static build served from ./dist via the ASSETS binding;
 * this Worker only handles one dynamic route — POST /api/views — which registers
 * a view for a path and returns the running total. Everything else falls through
 * to the static assets, so normal pages keep full CDN performance and cost no D1.
 *
 * The properties asked for:
 *   • bot filtering  — crawler User-Agents get no D1 access at all (not counted,
 *                      not even a read), so a crawl can't burn the row quota.
 *   • dedup          — one count per (IP, path) per UTC day, so refreshes and
 *                      same-visitor repeats don't inflate the number.
 *   • race-safety    — the increment is a single atomic D1 statement, and the
 *                      dedup insert (INSERT OR IGNORE) decides the winner under
 *                      concurrency, so simultaneous hits can't double-count.
 *
 * Abuse-resistance, so this public endpoint can't be turned against the site:
 *   • real pages only — a path is counted only if it resolves to an actual HTML
 *                       page (checked via the ASSETS binding), so junk paths
 *                       can't create unbounded rows in page_views (which, unlike
 *                       view_dedup, has no cleanup cron).
 *   • per-IP dedup    — the dedup key is IP+path+day (no User-Agent), so rotating
 *                       the UA header can't re-count the same path from one IP.
 *   • rate limits     — optional Workers rate-limit bindings cap how fast one
 *                       client (by IPv4 / IPv6 /64) can hit the endpoint, plus a
 *                       global backstop so a flood spread across many IPs still
 *                       can't run up D1 without bound (see wrangler.toml).
 *
 * No cookies, and no raw IP/User-Agent is ever stored: the dedup key is a salted
 * SHA-256 hash that the daily cron discards once its day has passed.
 */

// Naive crawler match — deliberately broad. Bots that run JS still won't be
// counted; bots that don't run JS never reach this endpoint at all.
const BOT_RE =
  /bot|crawl|spider|slurp|mediapartners|facebookexternalhit|embedly|quora link preview|pinterest|vkshare|w3c_validator|whatsapp|telegram|discordbot|headless|lighthouse|gptbot|ccbot|claudebot|bytespider|petalbot|ahrefs|semrush|mj12|dotbot|yandex/i;

// AI-training / bulk-scraper crawlers we BLOCK from the whole site (pages and
// images alike). robots.txt already asks them to stay out (src/pages/robots.txt.ts
// — keep this in sync with its BLOCK list), but robots.txt is advisory; this turns
// it into enforcement, so a crawler that ignores robots.txt still gets a 403 and
// can't download the photos. Deliberately matches only crawlers that fetch under
// these User-Agents — it excludes the robots.txt-only opt-out *tokens*
// (Google-Extended, Applebot-Extended), which never appear as a request UA, so
// real Googlebot / Bingbot / Applebot search (incl. Google Images) is untouched.
// Link-preview fetchers (facebookexternalhit, Twitterbot, …) are also not listed,
// so sharing previews keep working.
const BLOCKED_BOT_RE =
  /GPTBot|ClaudeBot|anthropic-ai|Claude-Web|CCBot|Meta-ExternalAgent|FacebookBot|Bytespider|ImagesiftBot|Diffbot|Omgili|PanguBot|cohere-ai|AI2Bot/i;

const MAX_PATH = 256;

// Reduce an incoming value to a safe, canonical site path or null if it's junk.
function normalizePath(p) {
  if (typeof p !== 'string') return null;
  try {
    if (p.includes('://')) p = new URL(p).pathname; // tolerate a full URL
  } catch {
    return null;
  }
  p = p.split('?')[0].split('#')[0];
  if (!p.startsWith('/') || p.length > MAX_PATH) return null;
  if (/[^\x20-\x7E]/.test(p)) return null; // ASCII printable only
  p = p.replace(/\/+$/, '');
  return p === '' ? '/' : p;
}

// Map a client IP to a rate-limit bucket: the full address for IPv4, but only the
// /64 prefix (first four groups) for IPv6 — a single IPv6 client typically gets a
// whole /64, so without this it could rotate addresses to dodge the per-client
// limit. Compressed forms ("2001:db8::1") are expanded so the prefix is exact.
function clientBucket(ip) {
  if (!ip) return 'noip';
  if (!ip.includes(':')) return ip; // IPv4: full address
  const [head, tail = ''] = ip.split('::');
  const headGroups = head ? head.split(':') : [];
  const tailGroups = tail ? tail.split(':') : [];
  const fill = Array(Math.max(0, 8 - headGroups.length - tailGroups.length)).fill('0');
  const groups = [...headGroups, ...fill, ...tailGroups];
  return 'v6:' + groups.slice(0, 4).map((g) => g || '0').join(':');
}

// Isolate-lifetime cache of paths already confirmed to be real pages. The set of
// pages can't change without a redeploy (which starts a fresh isolate), so once a
// path checks out we can skip the ASSETS round-trip on later hits — useful under a
// flood of repeats. Only positive results are cached, and it's capped, so a stream
// of distinct junk paths can't grow it.
const REAL_PAGES = new Set();

// Does this site path resolve to an actual HTML page? Asks the static-asset
// binding and accepts only a 2xx text/html response (following one trailing-
// slash redirect, which Astro's directory build can emit). Non-pages — a 404 for
// a junk path, or a non-HTML asset like an image/CSS/CSV — return false, so they
// are never counted and can't create rows in page_views. Returns true (fails
// open) if ASSETS is unavailable or errors, so a transient hiccup never silences
// the counter — the rate limit and dedup still bound any abuse.
async function isRealPage(env, origin, path) {
  if (REAL_PAGES.has(path)) return true;
  if (!env.ASSETS || typeof env.ASSETS.fetch !== 'function') return true;
  try {
    let res = await env.ASSETS.fetch(new Request(new URL(path, origin), { method: 'GET' }));
    if (res.status >= 300 && res.status < 400) {
      const loc = res.headers.get('location');
      res.body?.cancel?.();
      if (!loc) return false;
      res = await env.ASSETS.fetch(new Request(new URL(loc, origin), { method: 'GET' }));
    }
    const isPage = res.ok && (res.headers.get('content-type') || '').includes('text/html');
    res.body?.cancel?.();
    if (isPage && REAL_PAGES.size < 1024) REAL_PAGES.add(path);
    return isPage;
  } catch {
    return true;
  }
}

async function visitorKey(ip, path, day, salt) {
  const data = `${salt}|${ip}|${path}|${day}`;
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(data));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

async function handleViews(request, env) {
  if (request.method !== 'POST') return json({ error: 'method' }, 405);

  // Same-origin guard: a browser fetch from the site sends an Origin matching the
  // host. Deters casual off-site calls (not a hard boundary — headers can be
  // forged by non-browsers, but the rate limit + dedup + bot checks still bound
  // the damage).
  const url = new URL(request.url);
  const origin = request.headers.get('origin');
  if (origin) {
    try {
      if (new URL(origin).host !== url.host) return json({ error: 'origin' }, 403);
    } catch {
      return json({ error: 'origin' }, 403);
    }
  }

  // Bots never touch D1: crawlers are neither counted nor served a count, so a
  // crawl can't run up the row quota (and most don't execute this JS anyway).
  const ua = request.headers.get('user-agent') || '';
  if (!ua || BOT_RE.test(ua)) return json({ count: null, counted: false });

  // Reject oversized bodies before parsing — a real request is a few hundred
  // bytes ({"path":"/…"}); anything large is junk and shouldn't cost us a parse.
  if (Number(request.headers.get('content-length') || 0) > 1024) return json({ error: 'body' }, 413);

  const ip = request.headers.get('cf-connecting-ip') || '';

  // Two rate limits, both optional (the Worker skips a check if its binding is
  // absent; see wrangler.toml). Both are best-effort and counted per Cloudflare
  // location.
  //   • per-client — keyed by IPv4 address or IPv6 /64, so one client can't
  //                  hammer the endpoint (or rotate within its /64 to dodge it).
  //   • global     — a whole-endpoint backstop, so a flood spread across many IPs
  //                  still can't run the D1 write quota up without bound.
  if (env.RATE_LIMITER) {
    const { success } = await env.RATE_LIMITER.limit({ key: clientBucket(ip) });
    if (!success) return json({ error: 'rate' }, 429);
  }
  if (env.GLOBAL_LIMITER) {
    const { success } = await env.GLOBAL_LIMITER.limit({ key: 'all' });
    if (!success) return json({ error: 'busy' }, 429);
  }

  let path = null;
  try {
    const body = await request.json();
    path = normalizePath(body && body.path);
  } catch {
    path = null;
  }
  if (!path) return json({ error: 'path' }, 400);

  // Count only paths that resolve to a real page. Without this, any /junk path
  // would create a permanent row in page_views (which has no cleanup cron), so an
  // attacker could bloat the table. Unknown paths are treated as "not counted".
  if (!(await isRealPage(env, url.origin, path))) return json({ count: null, counted: false });

  const day = Math.floor(Date.now() / 86400000); // UTC epoch-day
  const salt = env.VIEW_SALT || 'xdqin-views';
  const key = await visitorKey(ip, path, day, salt);

  // Dedup: only the first (visitor, path, day) inserts a row. Under a race,
  // SQLite serializes writes, so exactly one insert reports changes === 1.
  const dedup = await env.DB.prepare('INSERT OR IGNORE INTO view_dedup (k, d) VALUES (?, ?)')
    .bind(key, day)
    .run();
  const firstToday = dedup.meta && dedup.meta.changes === 1;

  let count;
  if (firstToday) {
    // Atomic upsert increment — a single statement, so it's race-safe.
    const row = await env.DB.prepare(
      'INSERT INTO page_views (path, count) VALUES (?, 1) ' +
        'ON CONFLICT(path) DO UPDATE SET count = count + 1 RETURNING count'
    )
      .bind(path)
      .first();
    count = row ? row.count : 1;
  } else {
    const row = await env.DB.prepare('SELECT count FROM page_views WHERE path = ?')
      .bind(path)
      .first();
    count = row ? row.count : 0;
  }

  return json({ count, counted: firstToday });
}

export default {
  async fetch(request, env) {
    // Enforce the robots.txt block list: AI-training / bulk-scraper crawlers get
    // nothing — not pages, not images — even if they ignore robots.txt. Normal
    // search engines (Googlebot/Bingbot, incl. Google Images) aren't in the list,
    // so they pass straight through and discoverability is preserved.
    if (BLOCKED_BOT_RE.test(request.headers.get('user-agent') || '')) {
      return new Response('Not available to this crawler.', {
        status: 403,
        headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' },
      });
    }

    const url = new URL(request.url);
    if (url.pathname === '/api/views') {
      try {
        return await handleViews(request, env);
      } catch {
        return json({ error: 'server' }, 500);
      }
    }

    // security.txt (RFC 9116) is generated here rather than served as a static
    // asset so its required `Expires` field is recomputed on every request and
    // never goes stale — no annual edit or redeploy needed. The Worker is
    // already the request path for the whole site, so this costs nothing extra.
    if (url.pathname === '/.well-known/security.txt') {
      // ~1 year out; RFC 9116 recommends the value be less than a year ahead.
      const expires = new Date(Date.now() + 365 * 864e5).toISOString();
      const body = [
        '# Security policy for xdqin.com — https://www.rfc-editor.org/info/rfc9116',
        '',
        'Contact: https://example.com/security-contact',
        `Expires: ${expires}`,
        'Preferred-Languages: en, zh',
        'Canonical: https://xdqin.com/.well-known/security.txt',
        '',
      ].join('\n');
      return new Response(body, {
        headers: {
          'content-type': 'text/plain; charset=utf-8',
          'cache-control': 'public, max-age=86400',
          // The public/_headers security headers only apply to static-asset
          // responses, which this bypasses; nosniff is the one that matters for
          // a plain-text file, so set it here to match the site's baseline.
          'x-content-type-options': 'nosniff',
        },
      });
    }

    return env.ASSETS.fetch(request); // static site
  },

  // Daily housekeeping: only the current day's dedup rows are ever needed.
  async scheduled(_event, env, ctx) {
    const day = Math.floor(Date.now() / 86400000);
    ctx.waitUntil(env.DB.prepare('DELETE FROM view_dedup WHERE d < ?').bind(day).run());
  },
};
