/**
 * The two standard.site verification endpoints, as a drop-in route handler.
 *
 * They are served from the Worker rather than dropped into the static `public/`
 * directory for three reasons: the Worker is already the request path for every
 * request, so it costs nothing; the values stay in one config file instead of
 * being duplicated into a second place; and it sidesteps the question of
 * whether a given static-asset uploader carries a dot-prefixed directory at
 * all — a question with different answers on different hosts.
 *
 * Usage — call it first in your Worker's fetch, and fall through when it
 * returns null:
 *
 *   import { handleWellKnown } from './well-known.js';
 *
 *   export default {
 *     async fetch(request, env) {
 *       const wellKnown = handleWellKnown(request);
 *       if (wellKnown) return wellKnown;
 *       // …your other routes…
 *       return env.ASSETS.fetch(request);
 *     },
 *   };
 *
 * Both routes are guarded on their value being present and well-formed. When
 * one isn't configured the handler returns null and the request falls through
 * to the static assets, which 404 — the honest answer. Serving an empty body
 * would read as a *failed* verification rather than an absent one.
 */
import { did as ATPROTO_DID, publicationUri as PUBLICATION_URI } from '../atproto.config.js';

// A short, cacheable plain-text answer — the shape both endpoints want.
// nosniff matches the baseline a site's static responses usually carry, which
// doesn't reach anything the Worker generates itself.
//
// No trailing newline: consumers trim whitespace either way, but *absent* is
// the safer of the two — nothing breaks on a missing newline, while a strict
// parser could choke on an extra one.
function wellKnownText(body) {
  return new Response(body, {
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      // Rarely changes, but when it does (a handle move, a republished
      // publication) it should propagate the same hour, not the same week.
      'cache-control': 'public, max-age=3600',
      'x-content-type-options': 'nosniff',
    },
  });
}

/**
 * @param {Request} request
 * @returns {Response|null} a response for one of the two endpoints, or null if
 *   this request isn't one of them (or the value it needs isn't configured).
 */
export function handleWellKnown(request) {
  const url = new URL(request.url);

  // Handle verification: proves that whoever controls the domain controls this
  // DID, which is what lets the domain itself be the AT Protocol handle. A
  // `_atproto.<domain>` TXT record holding `did=did:plc:…` does the same job and
  // survives the site being down; either one is enough, and having both means
  // the claim stands if one is unreachable.
  if (url.pathname === '/.well-known/atproto-did' && ATPROTO_DID) {
    return wellKnownText(ATPROTO_DID);
  }

  // Publication verification: the other half of standard.site's two-way
  // handshake. An indexer that found a document record follows it to the
  // publication record, reads that record's `url`, comes back here, and only
  // trusts the document if this answers with the same publication AT-URI it
  // started from. Serving anything else — or a stale URI — silently invalidates
  // every post at once, not just one.
  if (url.pathname === '/.well-known/site.standard.publication' && PUBLICATION_URI) {
    return wellKnownText(PUBLICATION_URI);
  }

  return null;
}
