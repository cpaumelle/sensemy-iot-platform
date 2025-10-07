"""
WMC Gateway Scanner – Main Entrypoint
Version: 1.2.0
Last Updated: 2025-08-20 22:40 UTC
Authors: SenseMy IoT Team

Changelog:
- Mount /static for assets
- Add "/" route to render existing templates/index.html
- Keep existing routers (health, oauth2_routes, gateway_routes)
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

def create_app() -> FastAPI:
    app = FastAPI(title="WMC Gateway Scanner", version="1.2.0")

    # Static & templates
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except Exception:
        # In case the dir is not present in some envs
        pass
    templates = Jinja2Templates(directory="templates")

    # Root page -> render existing templates/index.html
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        try:
            return templates.TemplateResponse("index.html", {"request": request})
        except Exception:
            # Minimal fallback if template missing
            return HTMLResponse(
                "<h1>WMC Gateway Scanner</h1><p>Template not found.</p><p><a href=\"/docs\">/docs</a></p>",
                status_code=200,
            )

    # Routers — import inside factory to avoid circulars
    try:
        from app.routes import health as health_routes
        app.include_router(health_routes.router)
    except Exception:
        pass

    try:
        from app.routes.oauth2_routes import oauth2_router
        app.include_router(oauth2_router)
    except Exception:
        pass

    try:
        from app.routes.gateway_routes import gateway_router
        app.include_router(gateway_router)
    except Exception:
        pass

    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:create_app", factory=True, host="0.0.0.0", port=7300)
