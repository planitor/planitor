from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.models import User as DBUser
from planitor.schemas import User
from planitor.security import COOKIE_NAME, get_current_active_user
from planitor.templates import templates

router = APIRouter()


@router.get("/innskraning")
async def login_page(request: Request, redirect_to: str = ""):
    return templates.TemplateResponse(
        "login.html", {"request": request, "redirect_to": redirect_to}
    )


@router.get("/me/_error", response_model=User)
def get_user_error(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
):
    1 / 0


@router.get("/stillingar")
def get_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
):
    return templates.TemplateResponse(
        "account.html",
        {"request": request, "user": current_user},
    )


@router.get("/logout")
def logout(
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
