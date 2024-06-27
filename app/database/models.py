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

    user = relationship('Job', backref='user')


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)

    gpt_model = Column(String, nullable=False)
    language = Column(String, nullable=False)
    # gpt_model = Column("gpt_model_enum", Enum(GPTModelEnum, name="gpt_model_enum"), nullable=False)
    # language = Column("language_enum", Enum(LanguageEnum, name="language_enum"), nullable=False)
    prompt = Column(String, nullable=True)
    message = Column(String, nullable=True, default=None)
    gpt_result = Column(String, nullable=True, default=None)
    upload_path = Column(String, nullable=True, default=None)
    save_path = Column(String, nullable=True, default=None)

    status = Column("status_enum", Enum(StatusEnum, name="status_enum"), nullable=False, default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)

