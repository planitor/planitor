from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.routing import WebSocketRoute

from . import config
from .endpoints import router
from .endpoints.templates import templates

if config("DEBUG", cast=bool, default=False):
    import arel

    hotreload = arel.HotReload("templates")
    app = FastAPI(
        routes=[WebSocketRoute("/hot-reload", hotreload, name="hot-reload")],
        on_startup=[hotreload.startup],
        on_shutdown=[hotreload.shutdown],
    )
    templates.env.globals["hotreload"] = hotreload
else:
    app = FastAPI()
    app.add_middleware(SentryAsgiMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
