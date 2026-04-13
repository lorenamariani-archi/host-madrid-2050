from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
ASSETS_DIR = WEB_DIR / "assets"

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": "Small utility endpoints used to verify that the backend is running.",
    },
    {
        "name": "Demo Data",
        "description": "Original HOST endpoints that use local sample district and building data.",
    },
    {
        "name": "Official Madrid Data",
        "description": "Endpoints backed by official public sources such as Madrid Open Data, INE, and Catastro.",
    },
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="HOST Backend",
        description=(
            "Urban reuse analysis API for the HOST Madrid 2050 project.\n\n"
            "The API combines two modes:\n"
            "- demo routes that use local sample data for quick testing\n"
            "- real-data routes that assemble official public data from Madrid Open Data, "
            "INE, and Catastro\n\n"
            "For a TFG presentation, the easiest flow is to open `/app` for the visual interface or `/docs` for the API explorer, then try "
            "`/real/examples`, and then test `/real/district`, `/real/building/by-address`, "
            "and `/real/proposal`."
        ),
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
    )
    app.include_router(router)
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    @app.get("/app", include_in_schema=False)
    def frontend_app() -> FileResponse:
        """Serve the small HOST frontend used for demos and presentations."""

        return FileResponse(WEB_DIR / "index.html")

    return app


app = create_app()
