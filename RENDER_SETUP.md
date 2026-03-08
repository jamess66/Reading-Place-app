## Render Setup (Complete)

### 1) Push this repo to GitHub

Render deploys from a Git repository. Push your current code first.

### 2) Create service in Render

1. Open Render dashboard.
2. Click `New` -> `Blueprint`.
3. Select this repository.
4. Render will read [`render.yaml`](/Users/james/Projects/book-track/render.yaml) automatically.

### 3) Configure environment variable

In Render service settings, set:

- `THUNDERFOREST_API_KEY` = your Thunderforest key

If not set, app automatically falls back to CyclOSM tiles.

### 4) Deploy

Render uses:

- Build: `pip install -r requirements.txt`
- Start: `python app/app.py`
- Health check: `/healthz`

### 5) Verify

After deploy:

1. Open service URL.
2. Confirm app loads map.
3. Health endpoint should return `ok`:
   - `https://<your-service>.onrender.com/healthz`

### Notes

- Server binds using Render-provided `PORT`.
- Thunderforest key stays server-side only via tile proxy endpoint (`/tiles/cycle/{z}/{x}/{y}.png`).
