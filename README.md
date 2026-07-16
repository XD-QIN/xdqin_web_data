# xdqin_web_data

Companion data and code for the blogs at [xdqin.com](https://xdqin.com/blog/tech).

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


## License

All data and code in this repository are licensed under the
[Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
license. You may share and adapt the material for **non-commercial** purposes
with attribution; **commercial use is not permitted**. See the [`LICENSE`](LICENSE)
file for the full terms.
