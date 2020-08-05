from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.requests import Request
from starlette.routing import WebSocketRoute
from starlette.staticfiles import StaticFiles

from . import config
from .endpoints import router
from .endpoints.templates import templates


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


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/build", StaticFiles(directory="build"), name="build")
app.include_router(router)
