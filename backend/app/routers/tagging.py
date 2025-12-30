import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from app.database import get_db
from app.models import Music, TaggingQuestion, TaggingRecord, TaggingTask, User
from app.schemas import ApiResponse, ReviewResultEnum, TaggingQuestionOperate, TaggingQuestionResponse, OperationEnum, TaggingRecordResponse, TaggingRecordUpdate, TaggingStatusEnum, TaggingTaskOperate, TaggingTaskResponse, UserRoleEnum, BizException
from app.auth import get_current_user
from app.routers.user import user_to_response
from app.routers.music import music_to_response

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

@router.post("/question/operate")
def operate_tagging_question(
    operate: TaggingQuestionOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """操作打标题目"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")
    
    if operate.operation == OperationEnum.CREATE:
        return create_tagging_question(operate, db)
    elif operate.operation == OperationEnum.UPDATE:
        return update_tagging_question(operate, db)
    elif operate.operation == OperationEnum.DELETE:
        return delete_tagging_question(operate, db)
    else:
        raise BizException("无效的操作")

def create_tagging_question(
    operate: TaggingQuestionOperate,
    db: Session = Depends(get_db)
):
    """创建打标题目"""
    if not operate.title:
        raise BizException("标题不能为空")
    if db.query(TaggingQuestion).filter(TaggingQuestion.title == operate.title).first():
        raise BizException("标题已存在")

    db_question = TaggingQuestion(
        title=operate.title,
        description=operate.description,
        is_multiple_choice=operate.is_multiple_choice,
        options=operate.options
    )
    db.add(db_question)
    db.commit()
    return ApiResponse.success_response(db_question.id)

def update_tagging_question(
    operate: TaggingQuestionOperate,
    db: Session = Depends(get_db)
):
    """更新打标题目"""
    if not operate.id:
        raise BizException("打标题目ID不能为空")
    db_question = db.query(TaggingQuestion).filter(TaggingQuestion.id == operate.id).first()
    if not db_question:
        raise BizException("打标题目不存在")
 
    if operate.description:
        db_question.description = operate.description
    if operate.is_multiple_choice:
        db_question.is_multiple_choice = operate.is_multiple_choice
    if operate.options:
        db_question.options = operate.options
    db.commit()
    return ApiResponse.success_response()

def delete_tagging_question(
    operate: TaggingQuestionOperate,
    db: Session = Depends(get_db)
):
    """删除打标题目"""
    db_question = db.query(TaggingQuestion).filter(TaggingQuestion.id == operate.id).first()
    if not db_question:
        raise BizException("打标题目不存在")

    # 批量删除所有相关的打标记录
    db.query(TaggingRecord).filter(TaggingRecord.question_id == operate.id).delete()
    
    # 删除题目
    db.delete(db_question)
    db.commit()
    return ApiResponse.success_response()

@router.get("/question/list")
def list_tagging_question(
    db: Session = Depends(get_db)
):
    """获取打标题目列表"""
    return ApiResponse.success_response([tagging_question_to_response(tagging_question) for tagging_question in db.query(TaggingQuestion).order_by(TaggingQuestion.title.asc()).all()])


@router.post("/tag")
def tag_music(
    update: TaggingRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """打标音乐"""
    if current_user.role != UserRoleEnum.TAGGER and current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    if not update.id:
        raise BizException("打标记录ID不能为空")
    tagging_record = db.query(TaggingRecord).filter(TaggingRecord.id == update.id).options(joinedload(TaggingRecord.question), joinedload(TaggingRecord.task)).first()
    if not tagging_record:
        raise BizException("打标记录不存在")

    if tagging_record.task.status != TaggingStatusEnum.PENDING and tagging_record.task.status != TaggingStatusEnum.REJECTED:
        raise BizException("打标任务状态不正确")

    if not update.selected_options:
        raise BizException("打标选项不能为空")
    if not tagging_record.question.is_multiple_choice and len(update.selected_options) > 1:
        raise BizException("打标选项只能选择一个")

    tagging_record.selected_options = update.selected_options
    db.commit()
    return ApiResponse.success_response()

@router.post("/task/operate")
def operate_tagging_task(
    operate: TaggingTaskOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """操作打标任务"""
    if operate.operation == OperationEnum.CREATE:
        return create_tagging_task(operate, db, current_user)
    elif operate.operation == OperationEnum.DELETE:
        return delete_tagging_task(operate, db, current_user)
    elif operate.operation == OperationEnum.FINISH:
        return finish_tagging_task(operate, db, current_user)
    elif operate.operation == OperationEnum.REVIEW:
        return review_tagging_task(operate, db, current_user)
    else:
        raise BizException("无效的操作")

def create_tagging_task(
    operate: TaggingTaskOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建打标任务"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    if not operate.music_id:
        raise BizException("音乐ID不能为空")
    music = db.query(Music).filter(Music.id == operate.music_id).first()
    if not music:
        raise BizException("音乐不存在")

    if not operate.tagger_id:
        raise BizException("打标员ID不能为空")
    tagger = db.query(User).filter(User.id == operate.tagger_id, User.role.in_([UserRoleEnum.TAGGER, UserRoleEnum.ADMIN])).first()
    if not tagger:
        raise BizException("打标员不存在")
    if not operate.reviewer_id:
        raise BizException("审核员ID不能为空")
    reviewer = db.query(User).filter(User.id == operate.reviewer_id, User.role.in_([UserRoleEnum.REVIEWER, UserRoleEnum.ADMIN])).first()
    if not reviewer:
        raise BizException("审核员不存在")
    
    if not operate.question_ids:
        raise BizException("打标题目ID不能为空")
    questions = db.query(TaggingQuestion).filter(TaggingQuestion.id.in_(operate.question_ids)).all()
    if len(questions) != len(operate.question_ids):
        raise BizException("打标题目不存在")
    
    db_task = TaggingTask(
        music_id=operate.music_id,
        tagger_id=operate.tagger_id,
        reviewer_id=operate.reviewer_id,
        creator_id=current_user.id,
        status=TaggingStatusEnum.PENDING
    )
    db.add(db_task)
    db.flush()  # 刷新以获取 task_id
    for question in questions:
        db_record = TaggingRecord(
            task_id=db_task.id,
            question_id=question.id,
            selected_options=[]
        )
        db.add(db_record)
    db.commit()
    return ApiResponse.success_response(db_task.id)

def delete_tagging_task(
    operate: TaggingTaskOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除打标任务"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    if not operate.id:
        raise BizException("打标任务ID不能为空")
    db_task = db.query(TaggingTask).filter(TaggingTask.id == operate.id).first()
    if not db_task:
        raise BizException("打标任务不存在")

    db.query(TaggingRecord).filter(TaggingRecord.task_id == operate.id).delete()
    db.delete(db_task)
    db.commit()
    return ApiResponse.success_response()

def finish_tagging_task(
    operate: TaggingTaskOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """完成打标任务"""
    if current_user.role != UserRoleEnum.TAGGER and current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    if not operate.id:
        raise BizException("打标任务ID不能为空")
    db_task = db.query(TaggingTask).filter(TaggingTask.id == operate.id).first()
    if not db_task:
        raise BizException("打标任务不存在")
    if db_task.status != TaggingStatusEnum.PENDING and db_task.status != TaggingStatusEnum.REJECTED:
        raise BizException("打标任务状态不正确")

    db_task.status = TaggingStatusEnum.TAGGED
    db_task.tagger_id = current_user.id
    db_task.tagging_time = datetime.now(ZoneInfo("Asia/Shanghai"))
    db.commit()
    return ApiResponse.success_response()

def review_tagging_task(
    operate: TaggingTaskOperate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核打标任务"""
    if current_user.role != UserRoleEnum.REVIEWER and current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    if not operate.id:
        raise BizException("打标任务ID不能为空")
    db_task = db.query(TaggingTask).filter(TaggingTask.id == operate.id).first()
    if not db_task:
        raise BizException("打标任务不存在")
    if db_task.status != TaggingStatusEnum.TAGGED:
        raise BizException("打标任务状态不正确")

    # 检查审核结果
    if not operate.review_result:
        raise BizException("审核结果不能为空")

    # 审核打标记录
    if operate.review_result == ReviewResultEnum.AGREED:
        db_task.status = TaggingStatusEnum.REVIEWED
    elif operate.review_result == ReviewResultEnum.DISAGREED:
        db_task.status = TaggingStatusEnum.REJECTED
    else:
        raise BizException("审核结果不正确")
    db_task.reviewer_comment = operate.review_comment
    db_task.reviewer_id = current_user.id
    db_task.review_time = datetime.now(ZoneInfo("Asia/Shanghai"))
    db.commit()
    return ApiResponse.success_response()

@router.get("/task/list")
def list_tagging_task(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    status: TaggingStatusEnum | None = None,
    tagger_id: int | None = None,
    reviewer_id: int | None = None,
    db: Session = Depends(get_db)
):
    """获取打标任务列表（分页）"""
    query = db.query(TaggingTask)
    if keyword:
        query = query.filter(
            or_(
                TaggingTask.music.has(Music.filename.like(f"%{keyword}%")),
                TaggingTask.tagger.has(User.username.like(f"%{keyword}%")),
                TaggingTask.reviewer.has(User.username.like(f"%{keyword}%")),
                TaggingTask.creator.has(User.username.like(f"%{keyword}%"))
            )
        )
    if status:
        query = query.filter(TaggingTask.status == status)
    if tagger_id:
        query = query.filter(TaggingTask.tagger_id == tagger_id)
    if reviewer_id:
        query = query.filter(TaggingTask.reviewer_id == reviewer_id)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(TaggingTask.create_time.desc())
    query = query.options(
        joinedload(TaggingTask.music),
        joinedload(TaggingTask.tagger),
        joinedload(TaggingTask.reviewer),
        joinedload(TaggingTask.creator),
        selectinload(TaggingTask.records).joinedload(TaggingRecord.question)
    )
    task_list = query.offset(offset).limit(page_size).all()
    
    result = {
        "items": [tagging_task_to_response(tagging_task) for tagging_task in task_list],
        "total": total,
        "page": page,
        "page_size": page_size
    }
    return ApiResponse.success_response(result)

@router.get("/download")
def download_tagging_records(
    music_ids: list[int] = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出指定音乐的打标记录为 JSON 文件"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise BizException("无权限操作")

    music_list = db.query(Music).filter(Music.id.in_(music_ids)).options(
        selectinload(Music.tagging_tasks).joinedload(TaggingTask.tagger),
        selectinload(Music.tagging_tasks).selectinload(TaggingTask.records).joinedload(TaggingRecord.question)
    ).all()

    # 构建导出数据
    export_data = []
    for music in music_list:
        # 为每个音乐文件创建一个字典，键是问题，值是标注人员及其标注内容
        music_data = {}
        
        # 遍历该音乐的所有打标任务
        for task in [task for task in music.tagging_tasks if task.status == TaggingStatusEnum.REVIEWED]:
            # 遍历该任务的所有打标记录
            for record in task.records:
                if record.question.title not in music_data:
                    music_data[record.question.title] = {}
                music_data[record.question.title][task.tagger.username] = record.selected_options
        
        # 将音乐文件路径作为键，其打标数据作为值，添加到列表中
        export_data.append({
            music.filepath: music_data
        })
    
    # 转换为 JSON 字符串
    # indent=2 表示使用 2 个空格缩进，让 JSON 更易读
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    # 返回文件下载响应
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=tagging_records_{datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S")}.json"
        }
    )

def tagging_question_to_response(tagging_question: TaggingQuestion) -> TaggingQuestionResponse:
    return TaggingQuestionResponse(
        id=tagging_question.id,
        title=tagging_question.title,
        description=tagging_question.description,
        is_multiple_choice=tagging_question.is_multiple_choice,
        options=tagging_question.options,
        create_time=format_datetime_to_shanghai(tagging_question.create_time)
    )

def tagging_record_to_response(tagging_record: TaggingRecord) -> TaggingRecordResponse:
    return TaggingRecordResponse(
        id=tagging_record.id,
        question=tagging_question_to_response(tagging_record.question),
        selected_options=tagging_record.selected_options
    )

def tagging_task_to_response(tagging_task: TaggingTask) -> TaggingTaskResponse:
    return TaggingTaskResponse(
        id=tagging_task.id,
        music=music_to_response(tagging_task.music),
        status=tagging_task.status,
        tagger=user_to_response(tagging_task.tagger),
        tagging_time=format_datetime_to_shanghai(tagging_task.tagging_time),
        reviewer=user_to_response(tagging_task.reviewer) if tagging_task.reviewer else None,
        review_time=format_datetime_to_shanghai(tagging_task.review_time),
        creator=user_to_response(tagging_task.creator),
        create_time=format_datetime_to_shanghai(tagging_task.create_time),
        records=[tagging_record_to_response(record) for record in tagging_task.records]
    )