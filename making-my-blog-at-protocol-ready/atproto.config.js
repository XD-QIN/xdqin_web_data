// ────────────────────────────────────────────────────────────────────────────
//  AT Protocol identity + standard.site publication.
//
//  Fill in the three values below and the site becomes a verifiable
//  standard.site publication in the atmosphere: readers, indexers and Bluesky
//  link cards can resolve a post's URL to the record you signed for it, and
//  back again. Leave them empty and nothing changes — every consumer here
//  (link tags, /.well-known endpoints, the publisher script) is a no-op until
//  the value it needs is present and well-formed.
//
//  This file is plain JS at the repo root rather than a block in src/config.ts
//  because BOTH bundlers have to read it: Vite/Astro (for the <link> tags in
//  Layout.astro) and esbuild/wrangler (for the /.well-known routes in
//  worker/index.js). A .js module is the one shape both resolve without any
//  extra plumbing.
//
//  ── Setup, in order ───────────────────────────────────────────────────────
//   1. Get an account on any PDS (bsky.social or self-hosted). Note its DID —
//      `did:plc:…` — from Settings → Account, or
//      https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle=<you>
//   2. Put the DID in `did` below, and the handle you *want* in `handle`
//      (the domain itself is the handle).
//   3. Deploy. /.well-known/atproto-did now answers with the DID, which is what
//      proves the domain is yours. (A `_atproto.xdqin.com` TXT record holding
//      `did=did:plc:…` does the same job and keeps working if the site is down;
//      either one is enough, and DNS is the more robust of the two.)
//   4. In the Bluesky app: Settings → Handle → "I have my own domain" → verify.
//   5. Add ATP_APP_PASSWORD as a build *secret* in Cloudflare (Settings →
//      Build → Variables and secrets), from Settings → Privacy and security →
//      App passwords in Bluesky — never the account password.
//   6. Set Cloudflare's build command to `npm run build:deploy`, which
//      publishes before Astro builds. That's it: from here on, pushing a post
//      to the production branch publishes it and ships the page in one step.
//
//  To publish by hand instead — or to preview before any of the above:
//      npm run atproto:publish -- --dry-run        (no network, no credentials)
//      ATP_APP_PASSWORD=… npm run atproto:publish
//
//  See the README, "AT Protocol / standard.site", for the whole picture.
// ────────────────────────────────────────────────────────────────────────────

const config = {
  // The handle this site claims — the domain itself, once step 4 above is done.
  // Used as the default login identifier by scripts/atproto-publish.mjs and
  // shown in the README's setup output; nothing on the site depends on it.
  handle: '',

  // The DID that owns the records: the stable, rename-proof identifier for the
  // account. Served verbatim at /.well-known/atproto-did.
  did: '',

  // AT-URI of this site's `site.standard.publication` record. Served verbatim
  // at /.well-known/site.standard.publication, which is how an indexer confirms
  // the publication really is this domain's.
  //
  // Set ahead of the record existing, which is safe only because publishing is
  // part of the build: the rkey is the fixed `self`, so the URI is knowable in
  // advance, and the deploy that starts serving it runs *after* the publish
  // step that creates it. If publishing fails the build fails, so this endpoint
  // never goes live pointing at nothing. Publish by hand instead and you own
  // that ordering yourself — run the publisher before deploying.
  publicationUri: '',

  // How the blog introduces itself in reader apps — the body of the
  // publication record. Separate from `site` in src/config.ts on purpose: that
  // description covers the whole site, galleries included, while a publication
  // in standard.site is only the writing. Edit freely; the next
  // `npm run atproto:publish` pushes the change.
  publication: {
    name: 'Your Publication',
    description: 'What the blog is, in a sentence.',
  },
};

// ── Shapes ─────────────────────────────────────────────────────────────────
// Deliberately strict: a half-filled config should behave exactly like an empty
// one, never like a broken one. A malformed DID that still *renders* into a
// <link> tag would publish a claim this site can't back, so anything that
// doesn't match is treated as absent.

const DID_RE = /^did:[a-z]+:[a-zA-Z0-9._:%-]+$/;
// at://<did>/<collection nsid>/<rkey>
const AT_URI_RE = /^at:\/\/did:[a-z]+:[a-zA-Z0-9._:%-]+\/[a-zA-Z0-9.-]+\/[a-zA-Z0-9._~-]{1,512}$/;

/** @param {unknown} value */
export const isDid = (value) => typeof value === 'string' && DID_RE.test(value);

/** @param {unknown} value */
export const isAtUri = (value) => typeof value === 'string' && AT_URI_RE.test(value);

// The validated values. `null` means "not configured" — every consumer checks
// for that and stays silent rather than emitting a half-formed claim.
export const did = isDid(config.did) ? config.did : null;
export const handle = typeof config.handle === 'string' && config.handle ? config.handle : null;
export const publicationUri = isAtUri(config.publicationUri) ? config.publicationUri : null;

export default config;
