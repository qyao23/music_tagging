import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.schemas import BizException
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("data")
        if user_id is None:
            raise BizException("无效的 token")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise BizException("用户不存在")
        return user
    except jwt.JWTError:
        raise BizException("无效的 token")

def create_access_token(user_id: int):
    """创建访问令牌"""
    to_encode = {
        "data": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)