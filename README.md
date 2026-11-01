# Sarvam Dubber UI

Mobile-friendly web UI that **triggers the [sarvam-video-dubber](https://github.com/allanvarghese567-lab/sarvam-video-dubber) GitHub Action** (`Dub from URL`) and shows recent run status.

You paste a **direct video URL**, choose languages, and start the job. Progress and the `dubbed-output` artifact live on GitHub Actions.

## How it works

```
Phone / browser  →  this UI  →  GitHub API workflow_dispatch
                                      ↓
                         sarvam-video-dubber / Dub from URL
                                      ↓
                         download URL → Sarvam dub → artifact
```

- **Sarvam API key** stays as a secret on the *dubber* repo (`SARVAM_API_KEY`).
- This UI only needs a **GitHub token** that can dispatch workflows (`repo` + `workflow`).

## Setup

```bash
git clone https://github.com/allanvarghese567-lab/sarvam-dubber-ui.git
cd sarvam-dubber-ui

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
#   GITHUB_TOKEN=ghp_...   (classic PAT: repo, workflow)
#   GITHUB_OWNER=allanvarghese567-lab
#   GITHUB_REPO=sarvam-video-dubber
```

Also on the **dubber** repo:

1. Ensure `.github/workflows/dub-from-url.yml` is on `main`.
2. Settings → Secrets → Actions → `SARVAM_API_KEY`.

## Run locally

```bash
python app.py
# open http://127.0.0.1:8000
```

## Docker

```bash
docker build -t sarvam-dubber-ui .
docker run --rm -p 8000:8000 --env-file .env sarvam-dubber-ui
```

## Mobile test flow

1. Upload a short clip to any host that gives a **direct** file URL.
2. Open this UI on your phone.
3. Paste URL → target `ml-IN` → optional dry-run → **Start**.
4. Open the Actions link → watch logs (progress % prints from the dubber).
5. When green, download **dubbed-output** artifact.

## API

| Method | Path | Purpose |
|--------|------|----------|
| `GET` | `/` | UI |
| `GET` | `/api/health` | Config check |
| `POST` | `/api/trigger` | Dispatch workflow |
| `GET` | `/api/runs` | Recent workflow runs |
| `GET` | `/api/runs/{id}` | One run + jobs |

### Trigger body

```json
{
  "video_url": "https://example.com/clip.mp4",
  "target": "ml-IN",
  "src_lang": "en-IN",
  "dry_run": false
}
```

## Security notes

- Do **not** expose a powerful `GITHUB_TOKEN` on a public internet UI without auth.
- For a private test, run locally or behind a password / VPN / Cloudflare Access.
- Prefer a fine-scoped fine-grained PAT limited to the dubber repo, contents read + actions write.

## Host (free)

### Render (easiest)

1. Push this repo to GitHub (already done).
2. [Render](https://render.com) → **New → Blueprint** or **Web Service** → connect `sarvam-dubber-ui`.
3. Runtime: **Docker** (uses the included `Dockerfile`).
4. Set env vars:
   - `GITHUB_TOKEN` — PAT with `repo` + `workflow` (or fine-grained Actions write on the dubber repo)
   - `GITHUB_OWNER=allanvarghese567-lab`
   - `GITHUB_REPO=sarvam-video-dubber`
   - `WORKFLOW_FILE=dub-from-url.yml`
5. Deploy. Open the `*.onrender.com` URL on your phone.

Free tier spins down after idle; first request may take ~30–60s.

### Railway

1. [Railway](https://railway.app) → New Project → Deploy from GitHub.
2. Add the same env vars as above.
3. Railway sets `PORT` automatically; `app.py` already reads it.

### Security

Anyone who can open the public URL can trigger workflows with your token.
For a private test: use Render **private** service (paid), add basic auth, or keep the UI local/LAN only.

## License

MIT
