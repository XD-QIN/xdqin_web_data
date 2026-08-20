# Making My Blog AT Protocol Ready: standard.site Records from a Cloudflare Build

Code for the post **[Making My Blog AT Protocol Ready: standard.site Records from
a Cloudflare Build](https://xdqin.com/blog/tech/making-my-blog-at-protocol-ready)**,
which turns a static blog into a verifiable
[standard.site](https://standard.site) publication in the
[AT Protocol](https://atproto.com) network: each post becomes a signed
`site.standard.document` record under a DID you own, and the site and the records
verify each other.

These three files are the pieces that are worth lifting; the rest of the work is
a few lines each in your own layout and content schema, described in the post.

## Contents

| File | What it is |
|---|---|
| `atproto.config.js` | Identity config — handle, DID, publication URI. Ships empty. |
| `worker/well-known.js` | The two verification endpoints, as a drop-in route handler. |
| `scripts/atproto-publish.mjs` | The publisher: creates and updates the records. |

### `atproto.config.js`

The single source of truth, at your repo root. It's plain JavaScript rather than
JSON or a block in an existing config because **two bundlers have to read it**:
Vite (to render the `<link>` tags into your pages) and esbuild via Wrangler (to
bake the values into the Worker). A `.js` module is the one shape both resolve
without extra plumbing.

The validation at the bottom is the point of the file. A half-filled config
behaves exactly like an empty one, never like a broken one — a malformed DID that
still renders into a `<link>` tag publishes a claim the site cannot back, which
is worse than publishing nothing. Anything failing the pattern becomes `null`,
and every consumer treats `null` as "not configured" and stays silent.

Ships with empty values. This site's live ones are public if you want a filled-in
example:

```bash
curl https://xdqin.com/.well-known/atproto-did
curl https://xdqin.com/.well-known/site.standard.publication
```

### `worker/well-known.js`

Serves `/.well-known/atproto-did` (handle verification) and
`/.well-known/site.standard.publication` (publication verification) as plain
text. Call it first in your Worker's `fetch` and fall through when it returns
`null`; the file's header comment has the four-line example.

### `scripts/atproto-publish.mjs`

Dependency-free — `fetch` against four XRPC methods. Reads your posts'
frontmatter, writes one `site.standard.publication` record and one
`site.standard.document` per post, and writes each returned AT-URI back into that
post's frontmatter as `atUri`.

```bash
node scripts/atproto-publish.mjs --dry-run          # no network, no credentials
ATP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx node scripts/atproto-publish.mjs
```

| Flag | Effect |
|---|---|
| `--dry-run` | Build and print the records. No network, no credentials. |
| `--full-text` | Include each post's body as `textContent`. Off by default. |
| `--drafts` | Include posts marked `draft: true`. |
| `--section=<dir>` | Publish one content folder only. |
| `--skip-if-unconfigured` | Exit `0` when no DID is set, instead of failing. |
| `--production-branch=<name>` | Publish only from that branch, when the build environment names one. |

Three properties worth knowing before you adapt it:

- **No state file.** Record keys derive from the post (`<section>-<slug>`), so a
  second run *updates* the same records rather than creating duplicates.
- **No pointless writes.** Every write is a signed commit that goes out over the
  firehose, so each record is compared against what's already in the repo and
  skipped if identical — cover images included. The blob CID is computed locally
  (CIDv1 / raw / sha-256), so an unchanged image isn't even re-uploaded.
- **Metadata only, by default.** `textContent` embeds the whole post in the
  record, which lets reader apps render it without anyone visiting your site.
  That's a real trade, so it's behind a flag.

You will need to adapt `SECTIONS`, `SITE_URL` and `PUBLICATION_ICON` at the top
of the file to your own layout, and the frontmatter reader expects the shapes
described in the post (single-line scalars, flow or block lists). It fails loudly
on anything it doesn't understand, which is deliberate: a misread value becomes a
signed, published claim about a post, so "I don't understand line 7" has to beat
a plausible guess.

## Requirements

Node.js ≥ 18 for the publisher (it uses only built-ins: `fetch`, `node:crypto`,
`node:fs/promises`). An account on any PDS, and an **app password** — never your
account password.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), as with the rest
of this repository. See the root [`LICENSE`](../LICENSE).
