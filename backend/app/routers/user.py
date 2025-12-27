from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import timezone
from zoneinfo import ZoneInfo
from app.schemas import BizException
from app.database import get_db
from app.models import User
from app.schemas import ApiResponse, UserCreate, UserLogin, UserResponse, UserRoleEnum
from app.auth import get_current_user, create_access_token

router = APIRouter()

def format_datetime_to_shanghai(dt):
    """将 datetime 对象转换为上海时区的字符串"""
    if dt is None:
        return None
    # 如果 datetime 没有时区信息，假设它是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 转换为上海时区
    return dt.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """注册用户"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise BizException("用户已存在")
    db_user = User(username=user.username, password=user.password, role=user.role)
    db.add(db_user)
    db.commit()
    return ApiResponse.success_response(db_user.id)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user_by_name = db.query(User).filter(User.username == user.username).first()
    if not user_by_name:
        raise BizException("用户不存在")
    if user_by_name.password != user.password:
        raise BizException("密码错误")
    token = create_access_token(user_by_name.id)
    return ApiResponse.success_response(token)

@router.get("/")
def query_current_user(current_user: User = Depends(get_current_user)):
    """获取当前用户"""
    return ApiResponse.success_response(user_to_response(current_user))

@router.get("/list")
def list_users(
    keyword: str | None = None,
    role: UserRoleEnum | None = None,
    db: Session = Depends(get_db),
):
    """条件查询用户"""
    query = db.query(User)
    if keyword:
        query = query.filter(
            or_(
                User.id == int(keyword) if keyword.isdigit() else False,
                User.username.like(f"%{keyword}%")
            )
        )
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.username.asc()).all()
    return ApiResponse.success_response([user_to_response(user) for user in users])

def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        create_time=format_datetime_to_shanghai(user.create_time)
    )
