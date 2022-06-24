from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.routing import WebSocketRoute
from starlette.staticfiles import StaticFiles

from planitor.templates import templates

from . import config
from .endpoints import router

if config("DEBUG", cast=bool, default=False):
    import arel

    hotreload = arel.HotReload(paths=[arel.Path("./templates")])
    app = FastAPI(
        routes=[WebSocketRoute("/hot-reload", hotreload, name="hot-reload")],
        on_startup=[hotreload.startup],
        on_shutdown=[hotreload.shutdown],
    )
    templates.env.globals["hotreload"] = hotreload
else:
    app = FastAPI()
    app.add_middleware(SentryAsgiMiddleware)


@app.router.get("/")
async def get_index():
    return RedirectResponse("/s")


@app.router.get("/_error")
async def get_server_error(request: Request):
    return 1 / 0


@app.router.get("/_403")
async def get_permission_denied(request: Request):
    raise HTTPException(403)


css_path, js_path = [], []

dist_dir = Path(__file__).resolve().parent.parent / "dist"

for path in dist_dir.iterdir():
    if path.name.endswith(".js") and path.name.startswith("index"):
        js_path = f"/{path.name}"

for path in dist_dir.iterdir():
    if path.name.endswith(".css"):
        css_path = f"/{path.name}"


templates.env.globals.update({"css_path": css_path, "js_path": js_path})


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    """An exception handler for an improved browser experience."""
    if "application/json" not in request.headers.get("Accept", ""):
        if exc.status_code == 403:
            return RedirectResponse(
                request.url_for("login_page") + f"?redirect_to={request.url.path}"
            )
        template = "server_error.html"
        if exc.status_code == 404:
            template = "404.html"
        return templates.TemplateResponse(
            template,
            {"request": request, "detail": exc.detail},
            status_code=exc.status_code,
        )
    return await http_exception_handler(request, exc)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/dist", StaticFiles(directory="dist"), name="dist")
app.include_router(router)
