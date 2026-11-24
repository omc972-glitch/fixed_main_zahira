import os
import sys
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.zahira_konusmalar import DIALOGUES, GENERAL, SPRITE_FILES
from web.registry import EXPERIMENTS, run_experiment_adapter

app = FastAPI(title="Laboratuvar Simülasyon Merkezi")

app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "web", "static")), name="static")
app.mount("/assets/zahira", StaticFiles(directory=os.path.join(ROOT_DIR, "assets", "zahira")), name="zahira_assets")


class RunRequest(BaseModel):
    params: Dict[str, Any]


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(ROOT_DIR, "web", "static", "index.html"))


@app.get("/api/experiments")
def list_experiments():
    return [
        {
            "id": exp_id,
            "title": meta["title"],
            "subtitle": meta["subtitle"],
            "icon": meta["icon"],
            "accent": meta["accent"],
        }
        for exp_id, meta in EXPERIMENTS.items()
    ]


@app.get("/api/experiments/{exp_id}")
def get_experiment_detail(exp_id: str):
    if exp_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Deney bulunamadı.")
    meta = EXPERIMENTS[exp_id]
    zkey = meta["zahira_key"]
    _d = DIALOGUES.get(zkey, {})
    _intro = _d.get("intro") or _d.get("intro_resorsinol") or []
    intro = [{"sprite": s, "text": t} for s, t in _intro]
    return {
        "id": exp_id,
        "title": meta["title"],
        "subtitle": meta["subtitle"],
        "icon": meta["icon"],
        "accent": meta["accent"],
        "info_html": meta["info_html"],
        "parameters": meta["parameters"],
        "zahira": {
            "sprites": SPRITE_FILES,
            "intro": intro,
            "general": {
                k: [{"sprite": s, "text": t} for s, t in v]
                for k, v in GENERAL.items()
            },
        },
    }


@app.post("/api/experiments/{exp_id}/run")
def run_experiment(exp_id: str, req: RunRequest):
    if exp_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Deney bulunamadı.")
    try:
        return run_experiment_adapter(exp_id, req.params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simülasyon hatası: {e}")
