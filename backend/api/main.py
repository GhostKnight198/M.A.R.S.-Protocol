"""FastAPI surface. Engines never import FastAPI."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.pipeline import run_pipeline

app = FastAPI(title="M.A.R.S. Protocol API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_CACHE: dict = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/pipeline/run")
def pipeline_run() -> dict:
    try:
        return run_pipeline()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/mission/plan")
def mission_plan() -> dict:
    if "plan" not in _CACHE:
        _CACHE.update(run_pipeline())
    return _CACHE["plan"]


@app.get("/mission/report")
def mission_report() -> dict:
    if "report" not in _CACHE:
        _CACHE.update(run_pipeline())
    return _CACHE["report"]


@app.get("/mission/provenance")
def mission_provenance() -> dict:
    if "provenance" not in _CACHE:
        _CACHE.update(run_pipeline())
    return _CACHE["provenance"]