#!/usr/bin/env python3
"""Crunch registrars.csv into statistics for the spam-infrastructure report."""

import csv
import sys
from collections import Counter, defaultdict

# Domains that are clearly legitimate senders / infrastructure that ended up on
# the blocklist (recognizable brands or shared ESP infrastructure). Excluded
# from the spam-campaign statistics; listed separately in the report.
LEGIT = {
    "cnn.com", "garmin.com", "roku.com", "slb.com", "dunhamssports.com",
    "ezcontacts.com", "webofscience.com", "smtp.com", "ccsend.com",
    "herbertsmithfreehills.com", "constantcontact.com", "sendgrid.net",
}


def ns_provider(ns_field):
    """Reduce a nameserver hostname to its provider's registrable domain."""
    if not ns_field:
        return "(none)"
    first = ns_field.split(";")[0].strip().lower()
    if not first:
        return "(none)"
    parts = first.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return first


def norm_registrar(r):
    """Collapse trivial capitalization / suffix variants of the same registrar."""
    if not r:
        return r
    low = r.lower()
    if low.startswith("namecheap"):
        return "NameCheap, Inc."
    return r


STATUS_RANK = {"ok": 0, "no-registrar-field": 1, "not-found": 2}


def main(path):
    # Dedupe by domain: prefer an 'ok' row over an error/retry row.
    by_domain = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["registrar"] = norm_registrar(row["registrar"])
            d = row["domain"]
            prev = by_domain.get(d)
            if prev is None or STATUS_RANK.get(row["status"], 9) < STATUS_RANK.get(prev["status"], 9):
                by_domain[d] = row
    rows = list(by_domain.values())

    total = len(rows)
    ok = [r for r in rows if r["status"] == "ok" and r["registrar"]]
    legit = [r for r in rows if r["domain"] in LEGIT]
    spam = [r for r in ok if r["domain"] not in LEGIT]

    print(f"TOTAL ROWS: {total}")
    print(f"  resolved w/ registrar: {len(ok)}")
    print(f"  legit (excluded): {len(legit)}")
    print(f"  spam campaign: {len(spam)}")

    status_counts = Counter(r["status"] for r in rows)
    print("\nSTATUS:")
    for s, n in status_counts.most_common():
        print(f"  {n:4d}  {s}")

    reg = Counter(r["registrar"] for r in spam)
    print(f"\nREGISTRAR (spam only, n={len(spam)}):")
    for r, n in reg.most_common():
        print(f"  {n:4d}  ({100*n/len(spam):5.1f}%)  {r}")

    tld = Counter(r["domain"].split(".")[-1] for r in spam)
    print(f"\nTLD (spam only):")
    for t, n in tld.most_common(15):
        print(f"  {n:4d}  ({100*n/len(spam):5.1f}%)  .{t}")

    # registration month histogram
    months = Counter()
    years = Counter()
    for r in spam:
        c = r["created"]
        if c and len(c) >= 7:
            months[c[:7]] += 1
            years[c[:4]] += 1
    print(f"\nREGISTRATION YEAR (spam only):")
    for y, n in sorted(years.items()):
        print(f"  {y}  {n:4d}  ({100*n/len(spam):5.1f}%)")
    print(f"\nREGISTRATION MONTH (spam only, top 15):")
    for m, n in months.most_common(15):
        print(f"  {m}  {n:4d}  ({100*n/len(spam):5.1f}%)")

    # nameserver provider
    nsp = Counter(ns_provider(r["nameservers"]) for r in spam)
    print(f"\nNAMESERVER PROVIDER (spam only):")
    for p, n in nsp.most_common(15):
        print(f"  {n:4d}  ({100*n/len(spam):5.1f}%)  {p}")

    # cross-tab: registrar x top registration months
    print(f"\nTOP 5 REGISTRATION DATES (exact, spam only):")
    exact = Counter(r["created"] for r in spam if r["created"])
    for d, n in exact.most_common(8):
        print(f"  {d}  {n:4d}")

    # legit breakdown
    print(f"\nLEGIT DOMAINS FOUND ON BLOCKLIST ({len(legit)}):")
    for r in sorted(legit, key=lambda x: x["domain"]):
        print(f"  {r['domain']:30s}  {r['created'] or '----------':10s}  {r['registrar']}")

    # spam domains NOT through the dominant registrar (interesting outliers)
    dom_reg = reg.most_common(1)[0][0] if reg else None
    print(f"\nSPAM DOMAINS NOT VIA '{dom_reg}' ({sum(1 for r in spam if r['registrar']!=dom_reg)}):")
    for r in sorted((r for r in spam if r["registrar"] != dom_reg),
                    key=lambda x: x["registrar"]):
        print(f"  {r['domain']:30s}  {r['created'] or '----------':10s}  {r['registrar']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "registrars.csv")
