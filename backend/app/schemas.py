from enum import Enum
from pydantic import BaseModel
from typing import Any


class ApiResponse(BaseModel):
    """
    API 响应模型
    """
    success: bool = True
    data: Any | None = None
    error: str | None = None

    @classmethod
    def success_response(cls, data: Any | None = None) -> "ApiResponse":
        """
        成功响应
        """
        return cls(success = True, data = data)

    @classmethod
    def error_response(cls, error: str) -> "ApiResponse":
        """
        失败响应
        """
        return cls(success = False, error = error)


# 异常处理
class BizException(Exception):
    """
    业务异常
    """
    def __init__(self, error: str):
        self.error = error
        super().__init__(self.error)


class OperationEnum(Enum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    FINISH = "finish"
    REVIEW = "review"


class UserRoleEnum(Enum):
    """用户角色"""
    TAGGER = "tagger"  # 打标员
    REVIEWER = "reviewer"  # 审核员
    ADMIN = "admin"  # 管理员


class ReviewResultEnum(Enum):
    AGREED = "agreed"
    DISAGREED = "disagreed"


class TaggingStatusEnum(Enum):
    """打标状态"""
    PENDING = "pending"  # 待打标
    TAGGED = "tagged"  # 已打标
    REVIEWED = "reviewed"  # 已审核通过
    REJECTED = "rejected"  # 审核未通过


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRoleEnum


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRoleEnum
    create_time: str


class MusicResponse(BaseModel):
    id: int
    filepath: str
    filename: str
    duration: int
    valid_tagging_count: int
    create_time: str


class TaggingQuestionOperate(BaseModel):
    operation: OperationEnum
    id: int | None = None
    title: str | None = None
    description: str | None = None
    is_multiple_choice: bool | None = None
    options: list[str] | None = None


class TaggingQuestionResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    is_multiple_choice: bool
    options: list[str]
    create_time: str


class TaggingRecordUpdate(BaseModel):
    id: int
    selected_options: list[str]


class TaggingRecordResponse(BaseModel):
    id: int
    question: TaggingQuestionResponse
    selected_options: list[str]


class TaggingTaskOperate(BaseModel):
    operation: OperationEnum
    id: int | None = None
    music_id: int | None = None
    question_ids: list[int] | None = None
    tagger_id: int | None = None
    reviewer_id: int | None = None
    review_result: ReviewResultEnum | None = None
    review_comment: str | None = None


class TaggingTaskResponse(BaseModel):
    id: int
    music: MusicResponse
    status: TaggingStatusEnum
    tagger: UserResponse
    tagging_time: str | None = None
    reviewer: UserResponse | None = None
    review_time: str | None = None
    creator: UserResponse
    create_time: str
    records: list[TaggingRecordResponse]
