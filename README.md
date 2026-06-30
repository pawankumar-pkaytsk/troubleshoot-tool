# Meta Account Troubleshoot

Live tool to diagnose a seller account and generate a next-plan-of-action.

- **Frontend** — single static `index.html` (deployed on GitHub Pages). Two tracks
  (HITS / 1k–5k), Seller-ID lookup, and a 3-tab AI strategy
  (Website / Campaign / Out of the box).
- **Backend** — `backend/app.py` (FastAPI). Pulls live seller data from Metabase
  and generates the action plan with Claude.

**Live site:** https://pawankumar-pkaytsk.github.io/troubleshoot-tool/

The site runs standalone in **sample mode** with no backend. Connect the live
backend by appending `?api=https://your-host` to the URL (it's remembered in
`localStorage`).

## Data sources (Metabase, db 6)

| Card | What | Fields used |
|------|------|-------------|
| [7753](https://metabase.kaip.in/question/7753) seller_manager_mapping | Account team | GC, GM, KAE, KAM (+ growth lead, POCs…) |
| [10353](https://metabase.kaip.in/question/10353) Category Intelligence | Business details | company, website, contact, products / AOV / COGS at go-live |

## Run the backend locally

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Metabase + Anthropic creds
uvicorn app:app --reload --port 8000
```

Then open the site pointed at it:
`https://pawankumar-pkaytsk.github.io/troubleshoot-tool/?api=http://127.0.0.1:8000`

### Claude credentials

Two options in `backend/.env`:

- **Direct Anthropic** — key from https://console.anthropic.com (Settings → API keys);
  leave `ANTHROPIC_BASE_URL` unset.
- **Via a proxy (LiteLLM, etc.)** — set `ANTHROPIC_BASE_URL` to the proxy and use its
  key. Model name must exist on the proxy (check `GET {base_url}/v1/models`).

`CLAUDE_MODEL=claude-opus-4-8` is the default.

### API

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET  | `/api/health` | — | status + whether Claude/Metabase are configured |
| POST | `/api/seller` | `{seller_id, mode}` | merged mapping + business details |
| POST | `/api/plan`   | `{seller, mode}` | `{website[], campaign[], outside[]}` |

## Deploy the backend (so it's live for everyone)

The frontend is already live on Pages. To make the backend live, host
`backend/` on any of: **Render**, **Railway**, **Fly.io**, or an EC2 box, set the
same env vars, then point the site at `?api=https://your-deployed-host`.
