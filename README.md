# ComicCraft - AI Comic Story Creator (Vercel edition)

FastAPI serverless backend + static HTML/CSS/JS frontend.
Gemini writes the story, Hugging Face generates the panel images, fpdf2 builds the PDF.

## Structure

```text
api/index.py            FastAPI app (/api/health, /api/generate, /api/export)
services/               story, image and PDF logic
public/index.html       frontend (served statically by Vercel)
public/static/          style.css, script.js
vercel.json             function timeout (60s) + /api rewrite
requirements.txt        Python dependencies (no torch / diffusers)
```

## Deploy to Vercel

**Option A - GitHub (recommended)**
1. Push this folder's contents to a GitHub repo (the root of the repo must contain `vercel.json`).
2. Vercel dashboard -> Add New -> Project -> import the repo. Framework preset: **Other**.
3. Add environment variables (below), then Deploy.

**Option B - CLI**
```bash
npm i -g vercel
vercel          # preview
vercel --prod   # production
```

## Environment variables

| Name | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | optional | AI-written stories (built-in fallback story if missing) |
| `GEMINI_MODEL` | optional | default `gemini-2.5-flash` |
| `HF_TOKEN` | optional | AI panel images (placeholder images if missing) |
| `HF_IMAGE_MODEL` | optional | default `black-forest-labs/FLUX.1-schnell` |

The app works with no keys (fallback story + placeholder images), so you can verify the deployment first, then add keys and redeploy.

## What changed from the original project

- Removed `torch`, `diffusers`, `transformers`, `accelerate`: far too large for Vercel (250 MB limit) and no GPU there. Images now come from the Hugging Face Inference API.
- Vercel's filesystem is read-only/ephemeral, so nothing is saved to `generated/`. Panel images are returned as compressed JPEG data URLs and the PDF is built in memory.
- `/api/export` now takes JSON (not a form field) to avoid form-size limits.
- Images are generated in parallel (4 at a time) to stay inside the 60 s function limit. If a panel is not ready in time it falls back to a placeholder.
- Removed `__pycache__` and old generated PNGs.

## Local run

```bash
pip install -r requirements.txt uvicorn
npm i -g vercel && vercel dev      # closest to production
```
