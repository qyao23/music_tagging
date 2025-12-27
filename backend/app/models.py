from sqlalchemy import JSON, Boolean, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.schemas import TaggingStatusEnum, UserRoleEnum
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(Enum(UserRoleEnum))
    create_time = Column(DateTime(timezone = True), server_default = func.now())
    
    tagging_tasks = relationship("TaggingTask", foreign_keys="TaggingTask.tagger_id", back_populates="tagger")
    review_tasks = relationship("TaggingTask", foreign_keys="TaggingTask.reviewer_id", back_populates="reviewer")
    created_tasks = relationship("TaggingTask", foreign_keys="TaggingTask.creator_id", back_populates="creator")


class Music(Base):
    """音乐表"""
    __tablename__ = "music"

    id = Column(Integer, primary_key=True)
    filepath = Column(String)
    filename = Column(String, unique=True)
    duration = Column(Integer)
    create_time = Column(DateTime(timezone = True), server_default = func.now())

    tagging_tasks = relationship("TaggingTask", foreign_keys="TaggingTask.music_id", back_populates="music")


class TaggingQuestion(Base):
    """打标题目表"""
    __tablename__ = "tagging_questions"

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    description = Column(String)
    is_multiple_choice = Column(Boolean)
    options = Column(JSON)
    create_time = Column(DateTime(timezone = True), server_default = func.now())


class TaggingRecord(Base):
    """打标记录表"""
    __tablename__ = "tagging_records"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tagging_tasks.id"))
    question_id = Column(Integer, ForeignKey("tagging_questions.id"))
    selected_options = Column(JSON)

    task = relationship("TaggingTask", foreign_keys=[task_id], back_populates="records")
    question = relationship("TaggingQuestion", foreign_keys=[question_id])


class TaggingTask(Base):
    """打标任务表"""
    __tablename__ = "tagging_tasks"

    id = Column(Integer, primary_key=True)
    music_id = Column(Integer, ForeignKey("music.id"))
    status = Column(Enum(TaggingStatusEnum))
    tagger_id = Column(Integer, ForeignKey("users.id"))
    tagging_time = Column(DateTime(timezone = True))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewer_comment = Column(String)
    review_time = Column(DateTime(timezone = True))
    creator_id = Column(Integer, ForeignKey("users.id"))
    create_time = Column(DateTime(timezone = True), server_default = func.now())

    music = relationship("Music", foreign_keys=[music_id], back_populates="tagging_tasks")
    tagger = relationship("User", foreign_keys=[tagger_id], back_populates="tagging_tasks")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="review_tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    records = relationship("TaggingRecord", foreign_keys="TaggingRecord.task_id", back_populates="task")
