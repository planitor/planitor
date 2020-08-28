from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
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
    return RedirectResponse("/s/reykjavik")


@app.router.get("/_error")
async def get_server_error(request: Request):
    return 1 / 0


css_path, js_path = [], []

dist_dir = Path(__file__).resolve().parent.parent / "dist"

for path in dist_dir.iterdir():
    if path.name.endswith(".js") and path.name.startswith("index"):
        js_path = f"/{path.name}"

for path in dist_dir.iterdir():
    if path.name.endswith(".css"):
        css_path = f"/{path.name}"


templates.env.globals.update({"css_path": css_path, "js_path": js_path})


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/dist", StaticFiles(directory="dist"), name="dist")
app.include_router(router)
