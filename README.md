# xdqin_web_data

Companion data and code for the blogs at [xdqin.com](https://xdqin.com) — the
[Tech Blog](https://xdqin.com/blog/tech) and the
[Photo Blog](https://xdqin.com/blog/photography).

This repository holds the datasets and analysis scripts behind individual blog
posts, kept separate from the website source so the raw data and code can be
browsed, downloaded, and reproduced on their own. Each post that ships with data
gets its own folder, named after the post's URL slug.

## Contents

#### How I Built and Deployed My Photography Website

Folder: [`building-and-deploying-xdqin-com-on-cloudflare/`](building-and-deploying-xdqin-com-on-cloudflare)

Code for the post **[How I Built and Deployed My Photography Website: Astro on
Cloudflare Workers](https://xdqin.com/blog/tech/building-and-deploying-xdqin-com-on-cloudflare)**,
which deploys the static [astro-photo-folio](https://github.com/XD-QIN/astro-photo-folio)
template to Cloudflare Workers and adds a first-party, D1-backed page-view counter.
Includes the Worker (`worker/index.js`), the D1 schema (`migrations/0001_init.sql`),
and the Wrangler config (`wrangler.toml`). The `database_id` in `wrangler.toml` is a
placeholder — create your own D1 database and paste its id.

#### Who Is Behind My Blocked Spam Domains?

Folder: [`who-is-behind-my-blocked-spam-domains/`](who-is-behind-my-blocked-spam-domains)

Data and code for the post **[Who Is Behind My Blocked Spam Domains? An
RDAP-Based Statistical Analysis](https://xdqin.com/blog/tech/who-is-behind-my-blocked-spam-domains)**,
which looks up the registration record of more than a thousand blocked spam
domains via the Registration Data Access Protocol (RDAP) and clusters them by
registrar, registration date, top-level domain, and nameserver.

#### Building Film-Look Lightroom Presets

Folder: [`building-film-look-lightroom-presets/`](building-film-look-lightroom-presets)

Presets and code for the post **[Building Film-Look Lightroom Presets: The Colour
Science, and How to Test It](https://xdqin.com/blog/photography/building-film-look-lightroom-presets)**,
which measures the colour of four films frame by frame and builds presets against
those numbers. Includes **four ready-to-download presets** (`presets/*.xmp` — Autumn
Sonata, Green Ray 1986, Hero 2002, Pierrot le Fou) and `make_proxy.py`, which builds
the neutral proxy images the testing harness compares against. Independent work, not
affiliated with Adobe Inc.; see the folder's README for the full disclaimer.

#### A Colour Analysis of xMosaique's Eleven Built-In Presets

Folder: [`xMosaique-built-in-preset-colour-analysis-and-updates/`](xMosaique-built-in-preset-colour-analysis-and-updates)

Presets and measurement code for the post **[A Colour Analysis of xMosaique's Eleven
Built-In Presets: Reading a Look Off the Colour
Wheel](https://xdqin.com/blog/photography/xmosaique-built-in-preset-colour-analysis-and-updates)**,
which renders 187 probe colours through each of the eleven looks that ship in the
[xMosaique](https://xmosaique.com) camera app and reads the
resulting hue rotation, saturation and tonal response off a colour wheel, then
revises seven of them against those measurements. Includes **all eleven
ready-to-download presets** (`presets/*.xmp`) and the harness that produced every
figure (`analysis/`), with the measured data committed so the plots re-run without
building the rendering engine. Independent work, not affiliated with Adobe Inc.;
the film-inspired presets are original interpretations and name no manufacturer's
product. See the folder's README for the full disclaimer.

#### Making My Blog AT Protocol Ready

Folder: [`making-my-blog-at-protocol-ready/`](making-my-blog-at-protocol-ready)

Code for the post **[Making My Blog AT Protocol Ready: standard.site Records from
a Cloudflare Build](https://xdqin.com/blog/tech/making-my-blog-at-protocol-ready)**,
which turns the site into a verifiable [standard.site](https://standard.site)
publication in the [AT Protocol](https://atproto.com) network — each post becomes a
signed record under a DID, and the site and the records verify each other. Includes
the identity config (`atproto.config.js`), the two `/.well-known` verification
endpoints as a drop-in Worker route (`worker/well-known.js`), and the
dependency-free publisher (`scripts/atproto-publish.mjs`) that writes the records
and is wired into the deploy. `atproto.config.js` ships empty — fill in your own
handle, DID and publication URI; this site's live values are readable at its two
`/.well-known` endpoints.


## License

All data and code in this repository are licensed under the
[Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
license. You may share and adapt the material for **non-commercial** purposes
with attribution; **commercial use is not permitted**. See the [`LICENSE`](LICENSE)
file for the full terms.
