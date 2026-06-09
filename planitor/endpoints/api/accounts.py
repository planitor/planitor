from fastapi import Body, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from planitor import crud
from planitor.database import get_async_db
from planitor.endpoints.mail import send_reset_password_email
from planitor.models import User as DBUser
from planitor.schemas import Msg, Token, User
from planitor.security import (
    generate_password_reset_token,
    get_current_active_user,
    get_login_response,
    verify_password_reset_token,
)
from planitor.utils.passwords import get_password_hash

from . import router


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: DBUser = Depends(get_current_active_user),
):
    return current_user


@router.post("/login/access-token", response_model=Token, tags=["login"])
async def login_access_token(
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await crud.user.aauthenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Vitlaust netfang eða lykilorð.")
    elif not crud.user.is_active(user):
        raise HTTPException(
            status_code=400, detail="Þessi notandi hefur verið gerður óvirkur."
        )
    return get_login_response(user, response)


@router.post("/password-recovery/{email}", tags=["login"], response_model=Msg)
async def recover_password(
    request: Request, email: str, db: AsyncSession = Depends(get_async_db)
):
    user = await crud.user.aget_by_email(db, email=email.strip())

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Netfang fannst ekki.",
        )
    password_reset_token = generate_password_reset_token(email=email).decode()
    reset_url = request.url_for("reset_password")
    link = f"{reset_url}?token={password_reset_token}"
    send_reset_password_email(email_to=user.email, link=link)
    return {
        "msg": f"Tölvupóstur með leiðbeiningum hefur verið sendur á netfangið {user.email}."
    }


@router.post("/reset-password", tags=["login"], response_model=Token)
async def reset_password(
    response: Response,
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud.user.aget_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Netfang fannst ekki.",
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
    await db.commit()
    return get_login_response(user, response)
