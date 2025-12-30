import os
import json
from urllib.parse import quote
from datetime import timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session, selectinload
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import Response
from app.database import get_db
from app.models import Music, TaggingTask, TaggingRecord, User
from app.schemas import ApiResponse, MusicResponse, TaggingStatusEnum, UserRoleEnum, BizException
from app.auth import get_current_user

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

@router.post("/")
async def create_music(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过 JSON 文件上传音乐路径信息"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    file_paths: list[str] = []
    # 读取 JSON 文件内容
    content = await file.read()
    try:
        data = json.loads(content.decode('utf-8'))
        for file_path in data:
            file_paths.append(file_path)
    except json.JSONDecodeError as e:
        raise BizException("JSON 文件格式错误")
    
    # 支持的音频格式
    supported_formats = ['.mp3', '.wav']
    
    # 批量查询已存在的文件路径，避免逐条查询
    existing_paths = set()
    if file_paths:
        existing_records = db.query(Music.filepath).filter(Music.filepath.in_(file_paths)).all()
        existing_paths = {path[0] for path in existing_records}
    
    db_musics: list[Music] = []
    error_paths: list[str] = []
    
    for filepath in file_paths:
        # 检查是否已存在（使用批量查询的结果）
        if filepath in existing_paths:
            filename = os.path.splitext(os.path.basename(filepath))[0]
            error_paths.append(f"{filepath} (文件已存在: {filename})")
            continue
        
        # 验证文件格式
        _, ext = os.path.splitext(filepath)
        if ext.lower() not in supported_formats:
            error_paths.append(f"{filepath} (不支持的格式: {ext})")
            continue
        
        # 快速检查文件是否存在（不检查是否为文件，减少IO）
        if not os.path.exists(filepath):
            error_paths.append(f"{filepath} (文件不存在)")
            continue
        
        # 获取文件名（不带扩展名）
        filename = os.path.splitext(os.path.basename(filepath))[0]
        
        # 创建音乐记录
        db_music = Music(
            filepath=filepath,
            filename=filename
        )
        db_musics.append(db_music)
    
    # 批量添加成功的音乐记录
    if db_musics:
        db.add_all(db_musics)
        db.commit()
        success_ids = [db_music.id for db_music in db_musics]
    else:
        success_ids = []
    
    # 返回结果，包含成功和错误信息
    result = {
        "success_count": len(success_ids),
        "error_count": len(error_paths),
        "success_ids": success_ids,
        "error_paths": error_paths
    }
    
    return ApiResponse.success_response(result)

@router.delete("/")
def delete_music(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除音乐"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    # 查找音乐是否存在
    music = db.query(Music).filter(Music.id == id).first()
    if not music:
        raise BizException("音乐不存在")

    # 找到所有相关的打标任务ID
    tasks = db.query(TaggingTask.id).filter(TaggingTask.music_id == id).all()
    task_ids = [task.id for task in tasks]
    
    # 批量删除所有相关的打标记录（通过 task_id）
    if task_ids:
        db.query(TaggingRecord).filter(TaggingRecord.task_id.in_(task_ids)).delete()
    
    # 批量删除所有相关的打标任务
    db.query(TaggingTask).filter(TaggingTask.music_id == id).delete()
    
    # 删除音乐
    db.delete(music)
    db.commit()
    return ApiResponse.success_response()

@router.get("/")
def list_music(
    filename: str | None = None,
    db: Session = Depends(get_db)
):
    """获取音乐列表"""
    query = db.query(Music).options(selectinload(Music.tagging_tasks))
    if filename:
        query = query.filter(Music.filename.like(f"%{filename}%"))
    music_list = query.order_by(Music.filename.asc()).all()
    return ApiResponse.success_response([music_to_response(music) for music in music_list])

@router.get("/file")
def get_music_file(
    path: str,
    db: Session = Depends(get_db)
):
    """获取音乐文件（用于播放）"""
    if not os.path.exists(path):
        raise BizException("文件不存在")
    
    if not os.path.isfile(path):
        raise BizException("路径不是文件")
    
    # 验证文件是否在数据库中
    music = db.query(Music).filter(Music.filepath == path).first()
    if not music:
        raise BizException("音乐文件未注册")
    
    # 返回文件
    try:
        with open(path, 'rb') as f:
            content = f.read()
    except Exception as e:
        raise BizException(f"读取文件失败: {str(e)}")
    
    # 根据文件扩展名确定媒体类型
    _, ext = os.path.splitext(path)
    media_type = "audio/mpeg" if ext.lower() == ".mp3" else "audio/wav"
    
    # 编码文件名以支持中文字符（使用 RFC 5987 格式）
    filename = os.path.basename(path)
    encoded_filename = quote(filename, safe='')
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }
    )

def music_to_response(music: Music) -> MusicResponse:
    return MusicResponse(
        id=music.id,
        filepath=music.filepath,
        filename=music.filename,
        valid_tagging_count=sum(1 for task in music.tagging_tasks if task.status == TaggingStatusEnum.REVIEWED),
        create_time=format_datetime_to_shanghai(music.create_time)
    )
