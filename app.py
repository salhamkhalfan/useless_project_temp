"""Touch Grass - FastAPI server.

Upload a leaf photo -> vein graph pipeline -> R value -> long nature video.
"""
import os
import sys
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env (YOUTUBE_API_KEY, ...) if present.
def _load_dotenv():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_dotenv()

from main.vein_graph import process_leaf
from main.graph_utils import visualize_graph
from youtube import search_long_video

UPLOAD_DIR = ROOT / "live_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB

app = FastAPI(title="Touch Grass", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (ROOT / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/results/{job_id}/{filename}")
async def result_file(job_id: str, filename: str):
    path = UPLOAD_DIR / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "leaf.jpg")[1].lower()
    if ext not in ALLOWED_EXT:
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a JPG or PNG image of a leaf."},
        )

    data = await file.read()
    if not data or len(data) > MAX_BYTES:
        return JSONResponse(
            status_code=400,
            content={"error": "Image is empty or larger than 25 MB."},
        )

    job_id = uuid.uuid4().hex[:12]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir()

    input_path = job_dir / f"input{ext}"
    input_path.write_bytes(data)

    started = time.time()
    try:
        res = process_leaf(str(input_path), save=False, verbose=False)
    except Exception as exc:  # surface pipeline errors as friendly 422s
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=422,
            content={"error": f"Could not analyze this image: {exc}"},
        )
    elapsed = round(time.time() - started, 2)

    # Stage images
    skeleton = (res["skeleton"].astype(np.uint8)) * 255
    cv2.imwrite(str(job_dir / "skeleton.png"), skeleton)
    visualize_graph(res["graph"], str(job_dir / "overlay.jpg"),
                    background=res["image"])
    visualize_graph(res["graph"], str(job_dir / "clean.png"),
                    background=None)

    N, E, C = res["N"], res["E"], res["C"]
    mu, L, R = res["mu"], res["L"], res["R"]

    steps = [
        ("Detect veins", f"{res['method']}, threshold {res['threshold']}"),
        ("Nodes (junctions + ends)", f"N = {N}"),
        ("Edges (vein segments)", f"E = {E}"),
        ("Connected components", f"C = {C}"),
        ("Cyclomatic number", f"\u03bc = max(E - N + C, 1) = {mu}"),
        ("Total vein length (px)", f"L = {L}"),
        ("Complexity score", f"R = (N + E) * \u03bc + L = {R}"),
    ]

    video = search_long_video(R)

    return {
        "job_id": job_id,
        "elapsed": elapsed,
        "stats": {
            "N": N, "E": E, "C": C, "mu": mu, "L": L, "R": R,
            "method": res["method"],
            "threshold": res["threshold"],
            "connectivity": round(res["connectivity_ratio"], 3),
        },
        "steps": steps,
        "images": {
            "original": f"/results/{job_id}/input{ext}",
            "skeleton": f"/results/{job_id}/skeleton.png",
            "overlay": f"/results/{job_id}/overlay.jpg",
            "clean": f"/results/{job_id}/clean.png",
        },
        "video": video,
    }