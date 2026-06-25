#!/usr/bin/env python3
"""
Bulk RDAP lookup for blocked spam domains.

Captures registrar, registration (creation) date, and nameservers for each
registrable domain. Concurrent, with rate-limit handling, resume support, and
crash-safe incremental CSV writes.

Usage:
    python rdap_lookup.py blocked_domains.csv --out registrars.csv --direct
    python rdap_lookup.py blocked_domains.csv --out sample.csv --sample 30 --direct

Auto-resume: domains already present in --out (with a terminal status) are skipped.
On HTTP 429: backs off and retries up to MAX_RETRIES times.
"""

import argparse
import csv
import json
import os
import random
import sys
import threading
import time
import urllib.request
import urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

RDAP_ORG_URL = "https://rdap.org/domain/{}"
DIRECT_RDAP = {
    "com": "https://rdap.verisign.com/com/v1/domain/{}",
    "net": "https://rdap.verisign.com/net/v1/domain/{}",
}
TIMEOUT = 20
RATE_LIMIT_SLEEP = 20
MAX_RETRIES = 4
USER_AGENT = "rdap-lookup-script/2.0"

_write_lock = threading.Lock()
_print_lock = threading.Lock()


def parse_domains(path):
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()
    parts = [p.strip() for p in raw.replace("\r", "").replace("\n", ",").split(",")]
    out = []
    for p in parts:
        if not p or "." not in p:
            continue
        # skip the header label if present
        if p.lower() in ("blocked domain", "domain"):
            continue
        out.append(p)
    return out


def base_domain(d):
    parts = d.split(".")
    two_part_tlds = {"co.uk", "or.jp", "com.co", "co.jp", "co.in",
                     "com.au", "co.nz", "ne.jp", "org.uk", "ac.uk"}
    if len(parts) >= 3 and ".".join(parts[-2:]) in two_part_tlds:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return d


def get_tld(d):
    return d.split(".")[-1]


def build_url(domain, direct):
    if direct:
        tld = get_tld(domain)
        if tld in DIRECT_RDAP:
            return DIRECT_RDAP[tld].format(domain)
    return RDAP_ORG_URL.format(domain)


def extract(data):
    """Pull registrar / creation date / nameservers out of an RDAP record."""
    registrar = None
    for ent in data.get("entities", []) or []:
        if "registrar" in (ent.get("roles") or []):
            vcard = ent.get("vcardArray")
            if isinstance(vcard, list) and len(vcard) >= 2:
                for item in vcard[1]:
                    if isinstance(item, list) and len(item) >= 4 and item[0] == "fn":
                        registrar = item[3]
                        break
            if not registrar and ent.get("handle"):
                registrar = f"handle:{ent['handle']}"
        if registrar:
            break

    created = ""
    for ev in data.get("events", []) or []:
        if ev.get("eventAction") == "registration":
            created = (ev.get("eventDate") or "")[:10]
            break

    ns = []
    for n in data.get("nameservers", []) or []:
        name = n.get("ldhName")
        if name:
            ns.append(name.lower())

    return registrar, created, ";".join(ns)


def lookup(domain, direct=False):
    """Returns dict with domain, registrar, created, nameservers, status."""
    url = build_url(domain, direct)
    data = None
    status = "ok"
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_SLEEP * (attempt + 1))
                    continue
                status = "http-429"
            elif e.code == 404:
                status = "not-found"
            else:
                status = f"http-{e.code}"
            break
        except Exception as e:
            status = f"error:{type(e).__name__}"
            break

    if data is None:
        return {"domain": domain, "registrar": "", "created": "",
                "nameservers": "", "status": status}

    registrar, created, ns = extract(data)
    if registrar is None and status == "ok":
        status = "no-registrar-field"
    return {"domain": domain, "registrar": registrar or "", "created": created,
            "nameservers": ns, "status": status}


FIELDS = ["domain", "registrar", "created", "nameservers", "status"]


def load_existing(out_path):
    done = {}
    if not out_path or not os.path.exists(out_path):
        return done
    with open(out_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            st = row.get("status", "")
            if st in ("ok", "not-found", "no-registrar-field"):
                done[row["domain"]] = row
    return done


def write_header_if_needed(out_path):
    if not out_path:
        return
    if (not os.path.exists(out_path)) or os.path.getsize(out_path) == 0:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def append_row(out_path, row):
    if not out_path:
        return
    with _write_lock:
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(
                {k: row.get(k, "") for k in FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--out")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--direct", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    domains = parse_domains(args.file)
    unique = sorted(set(base_domain(d) for d in domains))
    print(f"Loaded {len(domains)} entries; {len(unique)} unique registrable domains",
          file=sys.stderr)

    if args.sample and args.sample < len(unique):
        random.seed(args.seed)
        targets = random.sample(unique, args.sample)
    else:
        targets = unique

    already = load_existing(args.out)
    todo = [d for d in targets if d not in already]
    print(f"Resuming {len(already)} done; querying {len(todo)} now "
          f"({args.workers} workers, direct={args.direct})\n", file=sys.stderr)

    write_header_if_needed(args.out)

    counts = Counter()
    for row in already.values():
        counts[row["registrar"] or f"[{row['status']}]"] += 1

    done_n = [0]
    total = len(todo)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(lookup, d, args.direct): d for d in todo}
        for fut in as_completed(futures):
            row = fut.result()
            append_row(args.out, row)
            label = row["registrar"] or f"[{row['status']}]"
            with _print_lock:
                done_n[0] += 1
                print(f"{done_n[0]:4d}/{total}  {row['domain']:42s}  "
                      f"{(row['created'] or '----------'):10s}  {label}")
                counts[row["registrar"] or f"[{row['status']}]"] += 1

    grand = sum(counts.values())
    print("\n" + "=" * 64)
    print(f"REGISTRAR CLUSTERING  ({grand} domains)")
    print("=" * 64)
    for reg, n in counts.most_common():
        pct = 100 * n / grand if grand else 0
        print(f"  {n:4d}  ({pct:5.1f}%)  {reg}")


if __name__ == "__main__":
    main()
