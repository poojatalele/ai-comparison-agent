"""FastAPI application factory.

Using a factory (rather than a module-level `app`) keeps construction explicit
and makes the app easy to build fresh inside tests.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .paths import FRONTEND_DIR
from .routes import api, pages, stores


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(
        title="OnPoint — Agentic Shopping Assistant",
        version="3.0.0",
        description=(
            "Compare a product's price across Indian retailers, see the onpoints "
            "you'd earn, and find a brand's nearest physical store."
        ),
    )

    # Routes
    app.include_router(pages.router)
    app.include_router(api.router)
    app.include_router(stores.router)

    # Static frontend assets
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    return app
