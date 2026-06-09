from fastapi import APIRouter, Depends, Request, Response

from planitor.models import User as DBUser
from planitor.schemas import User
from planitor.security import COOKIE_NAME, get_current_active_user
from planitor.templates import templates

router = APIRouter()


@router.get("/innskraning")
def login_page(request: Request, redirect_to: str = ""):
    return templates.TemplateResponse(
        "login.html", {"request": request, "redirect_to": redirect_to}
    )


@router.get("/me/_error", response_model=User)
async def get_user_error(
    current_user: DBUser = Depends(get_current_active_user),
):
    1 / 0


@router.get("/stillingar")
async def get_account(
    request: Request,
    current_user: DBUser = Depends(get_current_active_user),
):
    return templates.TemplateResponse(
        "account.html",
        {"request": request, "user": current_user},
    )


@router.get("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: DBUser = Depends(get_current_active_user),
):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/reset-password", tags=["login"])
def reset_password_html(request: Request, token: str):
    return templates.TemplateResponse(
        "password_recovery.html", {"request": request, "token": token}
    )
