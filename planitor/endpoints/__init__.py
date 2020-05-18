from fastapi import APIRouter

from . import city, accounts

router = APIRouter()
router.include_router(city.router)
router.include_router(accounts.router, prefix="/notendur")
