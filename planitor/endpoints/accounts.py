import datetime as dt

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from planitor import env
from planitor.database import get_db
from planitor.security import (
    cookie_auth,
    get_current_user,
    get_current_active_user,
    create_access_token,
    generate_password_reset_token,
    verify_password_reset_token,
)
from planitor.models import User as DBUser
from planitor.schemas import User, UserCreate, Token, Msg
from planitor.utils.passwords import get_password_hash
from planitor import crud

from .mail import send_reset_password_email

router = APIRouter()


@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
):
    return current_user


@router.post("/open", response_model=User)
def create_user_open(
    *,
    db: Session = Depends(get_db),
    password: str = Body(...),
    email: EmailStr = Body(...),
    full_name: str = Body(None),
):
    """ Create new user without the need to be logged in.
    """
    if not env.bool("USERS_OPEN_REGISTRATION", False):
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_in = UserCreate(password=password, email=email, full_name=full_name)
    user = crud.user.create(db, obj_in=user_in)
    return user


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
    access_token_expires = dt.timedelta(minutes=env("ACCESS_TOKEN_EXPIRE_MINUTES", 20))
    cookie_auth.get_login_response(user, response)  # set cookie for the browser
    return {
        "access_token": create_access_token(
            data={"user_id": user.id}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", tags=["login"], response_model=User)
def test_token(current_user: DBUser = Depends(get_current_user)):
    return current_user


@router.post("/password-recovery/{email}", tags=["login"], response_model=Msg)
def recover_password(email: str, db: Session = Depends(get_db)):
    user = crud.user.get_by_email(db, email=email.strip())

    if not user:
        raise HTTPException(
            status_code=404, detail="Netfang fannst ekki.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Tölvupóstur með leiðbeiningum hefur verið sendur."}


@router.post("/reset-password/", tags=["login"], response_model=Msg)
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
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    cookie_auth.get_login_response(user, response)  # set cookie for the browser
    return {"msg": "Lykilorð hefur verið uppfært."}


"""

@router.post("/", response_model=User)
def create_user(
    *, user_in: UserCreate, db: Session = Depends(get_db),
):
    user = crud.user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    if env.bool("EMAILS_ENABLED", False) and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    current_user: DBUser = Depends(get_current_active_user),
):
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


"""
