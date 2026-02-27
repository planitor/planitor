from fastapi import APIRouter

from . import accounts, api, city, debug, notifications
from .api import city as api_city
from .api import explore as api_explore
from .api import follow as api_follow
from .api import monitor as api_monitor
from .api import permits as api_permits
from .api import enums as api_enums
from .api import accounts as api_accounts

assert api_city
assert api_explore
assert api_follow
assert api_monitor
assert api_permits
assert api_enums
assert api_accounts


router = APIRouter()


router.include_router(city.router)
router.include_router(api.router, prefix="/api")
router.include_router(accounts.router, prefix="/notendur")
router.include_router(notifications.router, prefix="/tilkynningar")
router.include_router(debug.router, prefix="/__debug")
