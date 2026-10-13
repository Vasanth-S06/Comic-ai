import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from services.story_generator import generate_story
from services.image_generator import generate_panel_images
from services.exporters import build_comic_pdf

app = FastAPI(title="ComicCraft", version="1.1.0")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "ComicCraft",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "huggingface_configured": bool(os.getenv("HF_TOKEN")),
    }


@app.post("/api/generate")
def generate_comic(
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
    panels: int = Form(4),
):
    data = {
        "prompt": prompt.strip()[:1000],
        "character_name": character_name.strip()[:60],
        "setting": setting.strip()[:120],
        "tone": tone.strip()[:40],
        "art_style": art_style.strip()[:40],
        "panels": max(2, min(panels, 8)),
    }
    if not data["prompt"] or not data["character_name"] or not data["setting"]:
        return JSONResponse({"error": "Prompt, character and setting are required."}, status_code=400)

    story, story_ai = generate_story(data)
    image_urls, ai_images = generate_panel_images(story)

    for panel, url in zip(story["panels"], image_urls):
        panel["image_url"] = url

    notes = []
    if not story_ai:
        notes.append("Story used the built-in fallback (set GEMINI_API_KEY for AI stories).")
    if ai_images < len(image_urls):
        notes.append("Some images are placeholders (set HF_TOKEN for AI images).")

    return JSONResponse({
        "comic_id": uuid.uuid4().hex,
        "title": story["title"],
        "panels": story["panels"],
        "notice": " ".join(notes) or "AI-generated creative content. Review before publishing.",
    })


class ExportPayload(BaseModel):
    comic_id: str
    title: str
    panels: list[dict]


@app.post("/api/export")
def export_comic(payload: ExportPayload):
    if not payload.panels:
        return JSONResponse({"error": "No comic panels supplied."}, status_code=400)
    if len(payload.panels) > 8:
        return JSONResponse({"error": "Too many panels."}, status_code=400)

    safe_id = re.sub(r"[^A-Za-z0-9]", "", payload.comic_id)[:40] or "comic"

    try:
        pdf_bytes = build_comic_pdf(payload.title, payload.panels)
    except Exception as exc:
        return JSONResponse({"error": f"PDF generation failed: {exc}"}, status_code=500)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ComicCraft_{safe_id}.pdf"'},
    )
