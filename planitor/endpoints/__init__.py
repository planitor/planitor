from fastapi import APIRouter

from . import city, accounts, follow

router = APIRouter()
router.include_router(city.router)
router.include_router(follow.router, prefix="/subscriptions")
router.include_router(accounts.router, prefix="/notendur")
