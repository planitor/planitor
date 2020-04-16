"""
Planitor uses OAuth2PasswordBearer as the primary authentication method. But to allow
non-XHR browser requests to be authenticated too we actually return a token AND use the
set-cookie header upon login. See OAuth2PasswordOrSessionCookie.

"""

import datetime as dt
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN
from starlette.requests import Request

from planitor.database import get_db
from planitor.models.accounts import User
from planitor.session import CookieAuthentication
from planitor import env
from planitor import crud


ALGORITHM = "HS256"
access_token_jwt_subject = "access"


def create_access_token(*, data: dict, expires_delta: dt.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = dt.datetime.utcnow() + expires_delta
    else:
        expire = dt.datetime.utcnow() + dt.timedelta(minutes=15)
    to_encode.update({"exp": expire, "sub": access_token_jwt_subject})
    encoded_jwt = jwt.encode(to_encode, env.str("SECRET_KEY"), algorithm=ALGORITHM)
    return encoded_jwt


cookie_auth = CookieAuthentication()


class OAuth2PasswordOrSessionCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        payload = cookie_auth(request)
        if payload is not None:
            return payload
        return await super().__call__(request)


auth = OAuth2PasswordBearer(tokenUrl="/notendur/login/access-token")


def get_current_user(db: Session = Depends(get_db), token: str = Security(auth)):
    try:
        payload = jwt.decode(token, env.str("SECRET_KEY"), algorithms=[ALGORITHM])
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


def get_current_active_superuser(current_user: User = Security(get_current_user)):
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


password_reset_jwt_subject = "preset"


def generate_password_reset_token(email):
    delta = dt.timedelta(hours=env.int("EMAIL_RESET_TOKEN_EXPIRE_HOURS"))
    now = dt.datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": password_reset_jwt_subject, "email": email},
        env.str("SECRET_KEY"),
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, env.str("SECRET_KEY"), algorithms=["HS256"])
        assert decoded_token["sub"] == password_reset_jwt_subject
        return decoded_token["email"]
    except InvalidTokenError:
        return None
