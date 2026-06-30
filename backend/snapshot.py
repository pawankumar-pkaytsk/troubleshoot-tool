#!/usr/bin/env python3
"""Build the seller-data snapshot.

Runs ONE full scan per card (7753 + 10353 + 10362) — each returns ALL sellers —
and writes them to CACHE_DIR (backend/data/card_*.json.gz). The API then serves
every seller lookup from this snapshot with zero per-request BigQuery scan.

The heavy cards (10353/10362) scan ~15 GB each, so run this AT MOST once per day,
after the Metabase BigQuery daily quota resets (00:00 IST). Schedule it daily.

Usage:
    cd backend && source .venv/bin/activate
    python3 snapshot.py
"""
import app

if __name__ == "__main__":
    counts = app.refresh_all()
    for cid, n in counts.items():
        print(f"  card {cid}: {n:>6} sellers cached")
    print(f"snapshot written to {app.CACHE_DIR}")
