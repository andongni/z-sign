from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, status
from jwt import InvalidTokenError

from app import models
from app.api.deps import DbSession
from app.core.security import check_password, create_token, decode_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/")
def login(db: DbSession, payload: dict = Body(...)):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")

    user = (
        db.query(models.User)
        .filter(models.User.username == username, models.User.is_deleted.is_(False), models.User.is_active.is_(True))
        .first()
    )
    if not user or not check_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    user.last_login = datetime.now()
    db.commit()

    return {
        "access": create_token(str(user.id), "access"),
        "refresh": create_token(str(user.id), "refresh"),
    }


@router.post("/refresh/")
def refresh(payload: dict = Body(...)):
    token = payload.get("refresh")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh不能为空")

    try:
        decoded = decode_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token无效")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token类型无效")

    return {"access": create_token(str(decoded.get("sub")), "access")}

