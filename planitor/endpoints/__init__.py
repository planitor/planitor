from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from starlette.datastructures import Secret

from planitor import config
from planitor.mapkit import get_token as mapkit_get_token

from . import accounts, api, city, debug, notifications
from .api import city as api_city
from .api import follow as api_follow
from .api import monitor as api_monitor
from .api import permits as api_permits
from .api import enums as api_enums
from .api import accounts as api_accounts

assert api_city
assert api_follow
assert api_monitor
assert api_permits
assert api_enums
assert api_accounts


router = APIRouter()


@router.get("/mapkit-token")
async def mapkit_token(request: Request):
    return PlainTextResponse(
        mapkit_get_token(config("MAPKIT_PRIVATE_KEY", cast=Secret))
    )


router.include_router(city.router)
router.include_router(api.router, prefix="/api")
router.include_router(accounts.router, prefix="/notendur")
router.include_router(notifications.router, prefix="/tilkynningar")
router.include_router(debug.router, prefix="/__debug")
