"""
Planitor uses OAuth2PasswordBearer as the primary authentication method. But to allow
non-XHR browser requests to be authenticated too we actually return a token AND use the
set-cookie header upon login. However, only on GET request do we also consider session
cookies as valid credentials.

"""

import datetime as dt
from typing import Optional

from fastapi import Depends, HTTPException, Response, Security
from fastapi.security import APIKeyCookie, OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session
from starlette.datastructures import Secret
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN

from planitor import config, crud, ENV
from planitor.database import get_db
from planitor.models.accounts import User

EMAIL_RESET_TOKEN_EXPIRE_HOURS = config(
    "EMAIL_RESET_TOKEN_EXPIRE_HOURS", cast=int, default=2
)
ALGORITHM = "HS256"
COOKIE_NAME = "_planitor_auth"
access_token_jwt_subject = "access"

cookie_auth = APIKeyCookie(name=COOKIE_NAME, auto_error=False)
oauth2_auth = OAuth2PasswordBearer(
    tokenUrl="/notendur/login/access-token", auto_error=False
)


async def auth(request: Request) -> Optional[str]:
    """ On POST/PUT/DELETE do not use the cookie backend since we don’t have any XSS or
    CSRF protection. For endpoints that modify state we want tokens that are stored by
    the planitor client itself.

    """

    if request.method != "GET":
        return await oauth2_auth(request)
    for backend in [cookie_auth, oauth2_auth]:
        result = await backend(request)
        if result:
            return result


def get_login_response(user: User, response: Response) -> dict:
    """ set-cookie but also return oauth2 compatible login response """
    token = create_access_token({"user_id": user.id})
    response.set_cookie(
        COOKIE_NAME, token, path="/", secure=(ENV == "production"), httponly=True
    )
    return {
        "access_token": token,
        "token_type": "bearer",
    }


def create_access_token(data: dict, expires_delta: dt.timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = dt.datetime.utcnow() + expires_delta
    else:
        expire = dt.datetime.utcnow() + dt.timedelta(hours=24)
    to_encode.update({"exp": expire, "sub": access_token_jwt_subject})
    encoded_jwt = jwt.encode(to_encode, config("SECRET_KEY"), algorithm=ALGORITHM)
    return encoded_jwt.decode("utf-8")


def get_current_user(db: Session = Depends(get_db), token: str = Security(auth)):
    try:
        payload = jwt.decode(token, config("SECRET_KEY"), algorithms=[ALGORITHM])
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    user = crud.user.get(db, id=payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(current_user: User = Security(get_current_user)):
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: User = Security(get_current_user),
) -> User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_current_active_user_or_none(
    db: Session = Depends(get_db), token: str = Security(auth)
):
    """ HTML GET endpoints need this to render user/no-user versions of the same view.
    """
    try:
        payload = jwt.decode(token, config("SECRET_KEY"), algorithms=[ALGORITHM])
    except PyJWTError:
        return None
    user = crud.user.get(db, id=payload["user_id"])
    if not user or not crud.user.is_active(user):
        return None
    return user


password_reset_jwt_subject = "preset"


def generate_password_reset_token(email):
    delta = dt.timedelta(hours=EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = dt.datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": password_reset_jwt_subject, "email": email},
        config("SECRET_KEY", cast=Secret),
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token, config("SECRET_KEY", cast=Secret), algorithms=[ALGORITHM]
        )
        assert decoded_token["sub"] == password_reset_jwt_subject
        return decoded_token["email"]
    except InvalidTokenError:
        return None
