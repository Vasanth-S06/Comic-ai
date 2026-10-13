import base64
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

HF_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
WIDTH, HEIGHT = 768, 576  # 4:3, matches the UI and PDF layout
DEADLINE_SECONDS = 48


def _normalize_to_jpeg(raw_bytes):
    """Center-crop to 4:3, resize and compress to a small JPEG."""
    with Image.open(BytesIO(raw_bytes)) as img:
        img = img.convert("RGB")
        target = WIDTH / HEIGHT
        w, h = img.size
        if w / h > target:
            new_w = int(h * target)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
        out = BytesIO()
        img.save(out, format="JPEG", quality=82, optimize=True)
        return out.getvalue()


def _placeholder(index, text):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#efe9fb")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle([8, 8, WIDTH - 9, HEIGHT - 9], outline="#7146d9", width=4)
    draw.text((30, 28), f"ComicCraft preview - panel {index}", fill="#24134f", font=font)

    lines, current = [], ""
    for word in text.split():
        test = (current + " " + word).strip()
        if len(test) > 85:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    y = 70
    for line in lines[:14]:
        draw.text((30, y), line, fill="#4a4165", font=font)
        y += 22

    out = BytesIO()
    image.save(out, format="JPEG", quality=85)
    return out.getvalue()


def _hf_generate(prompt, token, timeout):
    url = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"
    body = json.dumps({"inputs": prompt}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "image/png",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _one_panel(args):
    index, panel, token, started = args
    prompt = (
        panel["image_prompt"]
        + ", high quality, coherent comic panel, detailed illustration, "
          "no words, no letters, no watermark"
    )
    if token:
        remaining = DEADLINE_SECONDS - (time.time() - started)
        if remaining > 5:
            try:
                raw = _hf_generate(prompt, token, timeout=min(remaining, 45))
                return _normalize_to_jpeg(raw), True
            except Exception:
                pass
    return _placeholder(index, panel["image_prompt"]), False


def generate_panel_images(story):
    """Returns (list_of_data_urls, count_of_ai_images)."""
    token = os.getenv("HF_TOKEN")
    started = time.time()
    jobs = [(i + 1, p, token, started) for i, p in enumerate(story["panels"])]

    with ThreadPoolExecutor(max_workers=min(4, len(jobs))) as pool:
        results = list(pool.map(_one_panel, jobs))

    urls, ai_count = [], 0
    for jpeg_bytes, is_ai in results:
        ai_count += 1 if is_ai else 0
        urls.append("data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode("ascii"))
    return urls, ai_count
