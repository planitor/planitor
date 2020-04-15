from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from .endpoints import router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.add_middleware(SentryAsgiMiddleware)
