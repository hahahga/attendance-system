"""
基础数据模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from flask_sqlalchemy import SQLAlchemy

# 从app包导入db实例
from app import db


class BaseModel(db.Model):
    """
    基础模型类，包含通用字段
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")