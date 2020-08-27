from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from planitor import crud
from planitor.database import get_db
from planitor.models import User as DBUser
from planitor.schemas import Msg, Token, User
from planitor.security import (
    COOKIE_NAME,
    generate_password_reset_token,
    get_current_active_user,
    get_current_user,
    get_login_response,
    verify_password_reset_token,
)
from planitor.templates import templates
from planitor.utils.passwords import get_password_hash

from .mail import send_reset_password_email

router = APIRouter()


@router.get("/innskraning")
def login_page(request: Request, redirect_to: str = ""):
    return templates.TemplateResponse(
        "login.html", {"request": request, "redirect_to": redirect_to}
    )


@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
):
    return current_user


@router.get("/stillingar")
def get_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
):
    return templates.TemplateResponse(
        "account.html", {"request": request, "user": current_user},
    )


@router.get("/logout")
def logout(
    response: Response,
    request: Request,
    current_user: DBUser = Depends(get_current_active_user),
):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.post("/login/access-token", response_model=Token, tags=["login"])
def login_access_token(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Vitlaust netfang eða lykilorð.")
    elif not crud.user.is_active(user):
        raise HTTPException(
            status_code=400, detail="Þessi notandi hefur verið gerður óvirkur."
        )
    return get_login_response(user, response)


@router.post("/login/test-token", tags=["login"], response_model=User)
def test_token(current_user: DBUser = Depends(get_current_user)):
    return current_user


@router.post("/password-recovery/{email}", tags=["login"], response_model=Msg)
def recover_password(request: Request, email: str, db: Session = Depends(get_db)):
    user = crud.user.get_by_email(db, email=email.strip())

    if not user:
        raise HTTPException(
            status_code=404, detail="Netfang fannst ekki.",
        )
    password_reset_token = generate_password_reset_token(email=email).decode()
    reset_url = request.url_for("reset_password")
    link = f"{reset_url}?token={password_reset_token}"
    send_reset_password_email(email_to=user.email, link=link)
    return {"msg": "Tölvupóstur með leiðbeiningum hefur verið sendur."}


@router.get("/reset-password", tags=["login"])
def reset_password_html(request: Request, token: str):
    return templates.TemplateResponse(
        "password_recovery.html", {"request": request, "token": token}
    )


@router.post("/reset-password", tags=["login"])
def reset_password(
    response: Response,
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404, detail="Netfang fannst ekki.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(
            status_code=400, detail="Þessi notandi hefur verið gerður óvirkur."
        )
    if len(new_password) < 5:
        raise HTTPException(
            status_code=400, detail="Lykilorðið þarf að vera a.m.k. 5 stafir."
        )
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return get_login_response(user, response)
