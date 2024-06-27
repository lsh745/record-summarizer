from sqlalchemy import Integer, String, DateTime, DateTime, Enum, ForeignKey
from sqlalchemy.sql.schema import Column
from sqlalchemy.orm import relationship
from utils.database_utils import Base
from database.enums import *
from pydantic import BaseModel
from datetime import datetime


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    slack_id = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    storage_access_token = Column(String, nullable=False)
    storage_secret_token = Column(String, nullable=False)

    user = relationship('Job', backref='user')


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)

    gpt_model = Column(String, nullable=False)
    language = Column(String, nullable=False)
    prompt = Column(String, nullable=True)
    message = Column(String, nullable=True, default=None)
    gpt_result = Column(String, nullable=True, default=None)

    bucket = Column(String, nullable=True, default=None)
    hash =  Column(String, nullable=True, default=None)
    source_path = Column(String, nullable=True, default=None)
    result_path = Column(String, nullable=True, default=None)

    status = Column("status_enum", Enum(StatusEnum, name="status_enum"), nullable=False, default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)

