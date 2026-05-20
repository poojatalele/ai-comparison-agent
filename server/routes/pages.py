"""Page routes — serve the single-page frontend."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from ..paths import FRONTEND_DIR

router = APIRouter(include_in_schema=False)


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/agent")


@router.get("/agent")
def agent_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@router.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "assets" / "favicon.ico")
