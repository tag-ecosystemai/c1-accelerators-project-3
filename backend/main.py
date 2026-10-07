from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from intelligence.agents.graph import build_graph


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


class AnalysisRequest(BaseModel):
    shipment_id: str = Field(
        ...,
        min_length=1,
        description="DataCo shipment/order identifier to investigate.",
    )


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(
    title="SentinelAI API",
    description="Supply-chain disruption intelligence and decision-support API.",
    version="1.0.0",
)

# Development support.
# Production uses the same origin because FastAPI serves the React build.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="sentinelai-api",
    )


@app.post("/api/analyze")
def analyze_shipment(request: AnalysisRequest) -> dict[str, Any]:
    shipment_id = request.shipment_id.strip()

    if not shipment_id:
        raise HTTPException(
            status_code=400,
            detail="Shipment ID cannot be empty.",
        )

    try:
        graph = build_graph()
        result = graph.invoke(
            {
                "shipment_id": shipment_id,
            }
        )

        return jsonable_encoder(result)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Required SentinelAI data is unavailable: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="SentinelAI analysis failed.",
        ) from exc


# Serve the production React application when frontend/dist exists.
#
# /assets is mounted separately so Vite-generated JS/CSS/assets are served
# directly by FastAPI.
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"

    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="frontend-assets",
        )


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    """
    Serve the React SPA.

    API routes are handled above. Any non-API browser route falls back
    to index.html so React Router/client-side navigation can work.
    """

    if full_path.startswith("api/"):
        raise HTTPException(
            status_code=404,
            detail="API endpoint not found.",
        )

    requested_file = FRONTEND_DIST / full_path

    if requested_file.is_file():
        return FileResponse(requested_file)

    index_file = FRONTEND_DIST / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(
        status_code=404,
        detail="Frontend build not found.",
    )