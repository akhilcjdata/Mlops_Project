# Stage 1 — GitHub push webhook receiver

Receives a GitHub `push`, verifies it's genuine, ignores non-`main` pushes, and
works out which files were **added / modified / removed**. It ACKs GitHub
immediately and logs the changed-file list in the background. That's the whole
job for this stage — chunk/embed/upsert come later.

## Files
- `main.py` — the FastAPI app (payload-based change resolution).
- `github_api.py` — reads file contents/trees via the GitHub REST API (no
  local git clone, no `git` binary required).
- `requirements.txt` — `fastapi` + `uvicorn`.

## 1. Install and run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Pick any random string; you'll paste the SAME value into GitHub later.
export GITHUB_WEBHOOK_SECRET="$(python -c 'import secrets;print(secrets.token_hex(16))')"
echo "$GITHUB_WEBHOOK_SECRET"        # copy this, you need it in step 3
export TARGET_BRANCH="main"          # optional, defaults to main

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Check it's alive: open http://localhost:8000/health -> `{"status":"ok"}`.

## 2. Expose it to the internet (tunnel)

GitHub can't reach `localhost`. Open a **second terminal** and start a tunnel.

**Cloudflare (recommended — stable-ish URL, no signup for quick tunnels):**
```bash
# install once: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared tunnel --url http://localhost:8000
```
It prints a public URL like `https://something-random.trycloudflare.com`.

**or ngrok:**
```bash
ngrok http 8000
```
Note: on ngrok's free plan the URL changes every restart, so you'll re-edit the
GitHub webhook each time. Cloudflare quick tunnels are less painful for dev.

Your **Payload URL** for GitHub = that public URL + `/webhook`, e.g.
`https://something-random.trycloudflare.com/webhook`.

## 3. Create the webhook on GitHub

Repo -> **Settings -> Webhooks -> Add webhook**:
- **Payload URL**: your tunnel URL + `/webhook`
- **Content type**: `application/json`   (important — not form-urlencoded)
- **Secret**: the exact `GITHUB_WEBHOOK_SECRET` value from step 1
- **Which events**: "Just the push event"
- **Active**: checked

Click **Add webhook**. GitHub immediately sends a `ping` — your terminal should
log `ping received` and the delivery goes green.

## 4. Test a real push

```bash
# in a clone of your dummy repo
echo "# change $(date)" >> README.md
git add . && git commit -m "test webhook" && git push origin main
```

Your uvicorn terminal should log something like:
```
[you/dummy-repo] refs/heads/main  1a2b3c4..5d6e7f8
  to index  (1): ['README.md']
  to delete (0): -
```

**Debugging tip:** on GitHub, **Settings -> Webhooks -> your hook -> Recent
Deliveries** shows every payload with its response, and each has a **Redeliver**
button — replay a delivery instead of pushing again while you iterate.

## What you'll see at the edges (expected, not bugs)
- **First push / new branch**: GitHub sends `before` = `0000...0`; the app logs
  "treat as FULL index" instead of a diff (you can't diff against nothing).
- **Push to another branch**: logged as "ignored branch" and skipped.
- **Bad/missing signature**: returns `401` (that's the security check working).

## What happens after the webhook connects
GitHub's initial `ping` (sent the instant you add the webhook) triggers an
automatic full index of the repo's existing code via `github_api.py` — no
local git clone involved, and it's skipped if the repo's already indexed.
Every push after that indexes just the changed files. See `bootstrap_repo_via_api.py`
if you want to force a manual (re-)index outside of the webhook flow.


cd c:\Project_Coding_Agent_RAG
.\env\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
cd c:\Project_Coding_Agent_RAG
.\tools\ngrok.exe http 8000