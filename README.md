# xdqin_web_data

Companion data and code for the tech blog at [xdqin.com](https://xdqin.com/blog/tech).

This repository holds the datasets and analysis scripts behind individual blog
posts, kept separate from the website source so the raw data and code can be
browsed, downloaded, and reproduced on their own. Each post that ships with data
gets its own folder, named after the post's URL slug.

## Contents

### Who Is Behind My Blocked Spam Domains?

Folder: [`who-is-behind-my-blocked-spam-domains/`](who-is-behind-my-blocked-spam-domains)

Data and code for the post **[Who Is Behind My Blocked Spam Domains? An
RDAP-Based Statistical Analysis](https://xdqin.com/blog/tech/who-is-behind-my-blocked-spam-domains)**,
which looks up the registration record of more than a thousand blocked spam
domains via the Registration Data Access Protocol (RDAP) and clusters them by
registrar, registration date, top-level domain, and nameserver.

| File | Description |
|---|---|
| `registrars.csv` | The raw RDAP lookup output — one row per blocked domain, with the columns described below. This is the dataset the post is based on. |
| `rdap_lookup.py` | Reads the blocklist, reduces each entry to its registrable domain, queries RDAP (Verisign directly for `.com`/`.net`), and writes `registrars.csv`. Concurrent, with rate-limit handling, resume support, and crash-safe incremental writes. |
| `analyze.py` | Crunches `registrars.csv` into the registrar / date / TLD / nameserver statistics reported in the post. |

`registrars.csv` columns:

| Column | Meaning |
|---|---|
| `domain` | The registrable domain that was looked up (e.g. `dunhamssports.com`). |
| `registrar` | The sponsoring registrar reported by RDAP, or empty if none was returned. |
| `created` | The registration (creation) date, `YYYY-MM-DD`, or empty if unavailable. |
| `nameservers` | Semicolon-separated nameserver hostnames from the RDAP record. |
| `status` | Lookup outcome: `ok`, `not-found`, `no-registrar-field`, `http-429`, or `error:<type>`. |

Reproduce the analysis with:

```bash
# Re-run the lookups from a blocklist (one domain per line / CSV):
python rdap_lookup.py blocked_domains.csv --out registrars.csv --direct

# Recompute the statistics from the dataset:
python analyze.py registrars.csv
```

Both scripts use only the Python 3 standard library.

## License

All data and code in this repository are licensed under the
[Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
license. You may share and adapt the material for **non-commercial** purposes
with attribution; **commercial use is not permitted**. See the [`LICENSE`](LICENSE)
file for the full terms.
