#!/usr/bin/env python3
"""
Minimal UI to trigger the Sarvam Video Dubber GitHub Action (dub-from-url.yml)
and poll run status. Designed for mobile + desktop.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = os.environ.get("GITHUB_OWNER", "allanvarghese567-lab")
REPO = os.environ.get("GITHUB_REPO", "sarvam-video-dubber")
WORKFLOW_FILE = os.environ.get("WORKFLOW_FILE", "dub-from-url.yml")
API = "https://api.github.com"

app = FastAPI(title="Sarvam Dubber UI", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


def _headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN is not configured on the server")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


class TriggerRequest(BaseModel):
    video_url: HttpUrl
    target: str = Field(default="ml-IN", description="Space-separated language codes")
    src_lang: str = Field(default="en-IN")
    dry_run: bool = False


class TriggerResponse(BaseModel):
    ok: bool
    message: str
    actions_url: str
    owner: str
    repo: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "owner": OWNER,
        "repo": REPO,
        "workflow": WORKFLOW_FILE,
        "token_configured": bool(GITHUB_TOKEN),
    }


@app.post("/api/trigger", response_model=TriggerResponse)
def trigger(body: TriggerRequest) -> TriggerResponse:
    url = f"{API}/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    payload = {
        "ref": "main",
        "inputs": {
            "video_url": str(body.video_url),
            "target": body.target.strip() or "ml-IN",
            "src_lang": body.src_lang.strip() or "en-IN",
            # workflow boolean inputs are accepted as JSON booleans
            "dry_run": body.dry_run,
        },
    }

    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, headers=_headers(), json=payload)
        if r.status_code not in (204, 200):
            raise HTTPException(
                status_code=502,
                detail=f"GitHub dispatch failed ({r.status_code}): {r.text}",
            )

    actions_url = f"https://github.com/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_FILE}"
    return TriggerResponse(
        ok=True,
        message="Workflow dispatched. Open Actions to watch progress; artifact appears when the run finishes.",
        actions_url=actions_url,
        owner=OWNER,
        repo=REPO,
    )


@app.get("/api/runs")
def list_runs(per_page: int = 10) -> dict[str, Any]:
    """Recent runs of the dub-from-url workflow."""
    url = f"{API}/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_FILE}/runs"
    params = {"per_page": min(per_page, 30)}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, headers=_headers(), params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GitHub runs failed: {r.text}")
        data = r.json()

    runs = []
    for run in data.get("workflow_runs", []):
        runs.append(
            {
                "id": run["id"],
                "status": run["status"],
                "conclusion": run.get("conclusion"),
                "html_url": run["html_url"],
                "created_at": run["created_at"],
                "updated_at": run["updated_at"],
                "display_title": run.get("display_title") or run.get("name"),
                "actor": (run.get("actor") or {}).get("login"),
            }
        )
    return {"runs": runs}


@app.get("/api/runs/{run_id}")
def run_detail(run_id: int) -> dict[str, Any]:
    url = f"{API}/repos/{OWNER}/{REPO}/actions/runs/{run_id}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, headers=_headers())
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=r.text)
        run = r.json()

        jobs_r = client.get(f"{url}/jobs", headers=_headers())
        jobs = jobs_r.json().get("jobs", []) if jobs_r.status_code == 200 else []

    return {
        "id": run["id"],
        "status": run["status"],
        "conclusion": run.get("conclusion"),
        "html_url": run["html_url"],
        "created_at": run["created_at"],
        "updated_at": run["updated_at"],
        "jobs": [
            {
                "name": j["name"],
                "status": j["status"],
                "conclusion": j.get("conclusion"),
                "started_at": j.get("started_at"),
                "completed_at": j.get("completed_at"),
            }
            for j in jobs
        ],
    }


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host=host, port=port, reload=False)
