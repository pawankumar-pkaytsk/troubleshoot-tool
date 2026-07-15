# Meta Account Troubleshoot — Team Handoff / Onboarding

Everything a teammate needs to **run, understand, extend, and deploy** this tool.

> **What it is:** enter a Seller ID → the tool pulls that seller's full picture from Metabase
> (team, business, category, daily metrics, weekly P&L, changelog, RTO, marketplace demand,
> last troubleshoot) and, with the uploaded Meta-ads CSV, has Claude generate a plain-English
> **next-plan-of-action** (Website / Campaign / Out-of-the-box / Scaleup) with an export button.

---

## 1. Links & access

| Thing | Value |
|---|---|
| **Live app (use this)** | https://troubleshoot-tool-sooty.vercel.app/ |
| GitHub Pages URL (auto-redirects to Vercel) | https://pawankumar-pkaytsk.github.io/troubleshoot-tool/ |
| GitHub repo | github.com/pawankumar-pkaytsk/troubleshoot-tool |
| Local clone | `~/troubleshoot-tool` |
| Hosting | **Vercel** — team `roopeshbanavath-5458`, project `troubleshoot-tool` (frontend + API, one origin) |
| AI | Claude via **LiteLLM proxy** `https://litellm.blitzshopdeck.in` (key `pawan-experiment`) |
| Data | **Metabase** `https://metabase.kaip.in` (Shopdeck warehouse) |
| Team-shared memory | **Upstash Redis** `great-ocelot-83816.upstash.io` |

**Access you must get from Pawan** (secrets — not in git): Metabase login, LiteLLM API key,
Upstash REST URL+token, and access to the Vercel project + the GitHub repo. All live values
already sit in **Vercel → project → Settings → Environment Variables** and in local `backend/.env`.

---

## 2. How it's built (architecture)

```
Browser (index.html, single file)
   │  fetch  (same origin)
   ▼
Vercel serverless function  ── api/index.py → backend/app.py (FastAPI)
   ├── Metabase (metabase.kaip.in)      ← all seller data (cards & dashboards)
   ├── LiteLLM proxy → Claude           ← the AI plan
   └── Upstash Redis                    ← team-shared plan memory
```

- **Frontend** = one file, `index.html` (HTML+CSS+JS, no build step). Served by Vercel's `/`
  route AND by GitHub Pages. The top of `index.html` redirects any non-vercel/non-localhost
  host to the Vercel URL (so the app is always same-origin — this fixed a persistent
  "Reconnecting" bug caused by cross-origin browser blocking).
- **Backend** = `backend/app.py` (FastAPI, stdlib-only Metabase client). One file.
- **Data caching:** the heavy Metabase cards return ALL sellers in one scan, cached to
  `backend/data/card_*.json.gz` (gitignored, bundled into the Vercel deploy). Per-seller cards
  are fetched on demand and cached in memory. **Never query the big cards per-seller in a loop.**

---

## 3. Run it locally

```bash
cd ~/troubleshoot-tool/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the real values (get from Pawan / Vercel env)
uvicorn app:app --reload --port 8000
```
Then open the frontend pointed at your local backend:
`http://localhost:8000/`  (the backend serves index.html at `/`), or the deployed UI with
`?api=http://127.0.0.1:8000`.

**Sample mode:** open `index.html` with `?api=` (empty) → runs on mock data, no backend/keys needed.

---

## 4. Deploy

Everything is committed to `main`. Two surfaces, both from the same repo:

```bash
cd ~/troubleshoot-tool
git add -A && git commit -m "..." && git push        # updates GitHub Pages (redirector)
npx vercel deploy --prod --yes                        # updates the LIVE app (Vercel)
```
- Vercel CLI is already authenticated locally and the project is linked (`.vercel/`).
- `vercel.json` sets `maxDuration: 120` (plan calls take ~45s).
- The Vercel deploy **bundles `backend/data/*.json.gz`** (the seller-data snapshot) even
  though it's gitignored — so a fresh snapshot needs a redeploy to go live.

---

## 5. Environment variables (Vercel + backend/.env)

| Var | Purpose |
|---|---|
| `METABASE_URL` / `METABASE_USER_EMAIL` / `METABASE_PASSWORD` | Metabase auth |
| `ANTHROPIC_BASE_URL` | `https://litellm.blitzshopdeck.in` (the LiteLLM proxy) |
| `ANTHROPIC_API_KEY` | LiteLLM key (`pawan-experiment`, ~$15 budget) |
| `CLAUDE_MODEL` | default model (`claude-opus-4-8`) |
| `PLAN_MODEL` | single-pass plan model (defaults to CLAUDE_MODEL) |
| `ANALYST_MODEL` / `SPECIALIST_MODEL` / `SYNTH_MODEL` | legacy multi-agent tiers (unused now) |
| `FUNDS_MODEL` | cheap model for the funds ping (`claude-haiku-4-5-20251001`) |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | team-shared memory + methodology KB |
| `CACHE_DIR` (`/tmp/ts_cache`), `ALLOW_LIVE_PULL`, `BULK_TTL`, `REFRESH_TOKEN` | caching controls |

To change cost/quality of the plan: set `PLAN_MODEL=claude-sonnet-4-6` (cheaper/faster) or
`claude-opus-4-8` (deepest). One env change, redeploy.

---

## 6. Data sources — every Metabase card/dashboard and what it feeds

**Bulk-cached cards** (pulled param-less = all sellers in one scan; in `CARDS` tuple → nightly snapshot):

| Card | Feeds |
|---|---|
| 7753 | Account team — GC / GM / KAE / KAM (+ POCs) |
| 10353 | Business details (company, website, contact, offers, products/AOV/COGS at go-live) |
| 10352 | Lighter business card — website/company/contact backup for 10353 |
| 10773 (db6) | Daily metrics time series — spend / CPM / CTR / s_gmv / orders / gmv + PQ (lifetime_avg_pq, last_15d_avg_pd) |
| 11011 | Weekly P&L — w1/w2/w3 spend + P&L% + best_source → **buckets** |
| 10189 | Last troubleshoot — date, type, `last_ts_actions` text, last-7d spend |
| 2497 (db2) | **COGS** (`cosgs`) + live SKUs |
| 2787 (db2) | Spend — today / yesterday / lifetime + first date |
| 10065 (db2) | Spend — total + first/last date (⚠ key column is `seller id` with a space) |

**Per-seller cards** (need seller_id; fetched on demand, cached):

| Source | Feeds |
|---|---|
| 3757 (db6) | **Category** — aggregated to the dominant `l1>l2>l3>l4` product chain. (Card 10362 broke, 3773 was incoherent — 3757 is the correct one.) |
| 1880 (db2) | **Auto P&L CSV** (recent 26 wks) + **AOV** (from the recent week with spend>3540) + **cancellation** (avg cancelled_perc of recent 2 weeks) |
| 3425 / dashboard 398 (db6) | **Marketplace demand** — per-product ratings → Run/Test/Hold campaign flags |

**Dashboards fetched via `/api/insights` (lazy, db2, cheap):**

| Dashboard | Feeds |
|---|---|
| 96 (Change Log) | Recent changes (coupon/meta/payment/product-page/shipping/website/catalogue/comms/google) |
| 266 (City-wise RTO) | RTO by city → exclude high-RTO cities |
| 187 (LP/courier-wise RTO) | RTO by courier |

**Hard-coded:** category benchmarks (RTO/COGS/AOV/etc. per L2 category) live in
`backend/benchmarks.py` (from a Shopdeck CSV) — refresh by regenerating that file.

---

## 7. The AI plan (how it works)

- Endpoint `POST /api/plan` (stage `full` = the one used). Single Claude call, ~45s.
- Inputs: the seller object (all data above) + uploaded **Meta ads CSV** + auto P&L + optional extra CSVs.
  Large row-level CSVs are **aggregated by campaign** server-side (`_summarize_csv`) so the model
  doesn't choke on 4,000+ rows.
- Output (forced tool-use, structured): `website`, `campaign`, `outside`, `scaleup` (1k-5k track only),
  plus `summary` and `top_priorities`. Capped ≤8 actions/category.
- The prompt injects the **troubleshooting methodology** (from `_get_methodology()`, editable in
  Upstash `kb:methodology`), the **2K→5K scaling playbook**, a **learning review** vs the last plan
  (IMPROVED / WORSENED / REVERT / KEEP), and **mandatory flags** (e.g. cancellation >5% → forced action).
- **Memory:** each plan is saved to Upstash (`plan:<seller_id>`, last 8) and fed back on the next run
  (team-shared). See `/api/memory`.

---

## 8. Nightly refresh

Scheduled task `troubleshoot-tool-snapshot` (~01:09 daily, after the BigQuery quota resets at
00:00 IST) runs `backend/snapshot.py` (rebuilds `backend/data/*.json.gz` = all bulk cards) then
`npx vercel deploy --prod` so fresh data goes live. Manual: run those two commands, or hit the
token-protected `POST /api/refresh`.

---

## 9. How to extend (add a new data point) — the repeatable recipe

This is the pattern used for every card above:

1. **Inspect the card** in Metabase: note its `id`, `database_id`, columns, and params
   (seller_id param id, etc.). Check if the seller filter is optional (→ bulk-cacheable) or
   required (→ per-seller).
2. **Backend (`app.py`):**
   - If all-sellers/bulk → add the card id to the `CARDS` tuple; it auto-caches + snapshots.
   - If per-seller → add a `_get_x(seller_id, ...)` fetcher (copy `_get_demand` / `_get_rto`).
   - Add the field(s) to the `/api/seller` (or `/api/insights`) response.
3. **Frontend (`index.html`):** add a card/section builder + render it; add mock data so sample
   mode shows it.
4. **(Optional) Plan:** if the AI should use it, mention the new field in the plan prompt.
5. **Test → commit → `git push` + `npx vercel deploy --prod --yes`.**

---

## 10. Known gotchas

- **BigQuery daily quota:** db6 cards each scan ~15 GB. That's why they're pulled once (all
  sellers) and cached, never per-seller in a loop. Quota resets 00:00 IST.
- **Vercel 60s→120s:** plan is a single ~45s call; keep it that way (a previous multi-agent
  version 504'd). Big CSVs are aggregated to stay fast.
- **LiteLLM budget:** the funds badge (top-right) shows remaining $. When it's low, recharge the
  `pawan-experiment` key or the plan calls 429.
- **Cross-origin:** always use the Vercel URL. Pages redirects there because browser privacy
  settings block Pages→Vercel API calls.
- **Card 10065** uses `seller id` (with a space) as its key column — handled in `_pull_card_all`.

---

## 11. Data still awaited / to confirm
- **Learning & Training dept view** (GC onboarding from card 11431; month dropdown; GC-wise bucket
  health / spend-live / live-assigned / task-adherence-SLA / golive / callback-SLA / HITS target vs
  achieved) — requested, not yet built; several of those metrics need their Metabase cards identified.
- Confirm "LP" on dashboard 187 = Logistics Partner (courier), not Landing Page.

---
_Maintainer: Pawan. Built with Claude Code. Everything lives in one repo (`~/troubleshoot-tool`):
`index.html` (frontend) + `backend/app.py` (API) + `backend/benchmarks.py` + `backend/snapshot.py`._
