"""
数据库核心模块
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_database_url


# 创建数据库引擎
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # 在生产环境中关闭SQL日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建所有表
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    删除所有表
    """
    Base.metadata.drop_all(bind=engine)


def reset_database():
    """
    重置数据库（删除并重新创建所有表）
    """
    drop_tables()
    create_tables()


def init_db():
    """
    初始化数据库，创建所有表
    """
    create_tables()


def get_session() -> Session:
    """
    获取数据库会话（非依赖注入方式）
    """
    return SessionLocal()


def commit_and_refresh(db: Session, obj):
    """
    提交并刷新对象
    """
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def commit_and_close(db: Session):
    """
    提交并关闭会话
    """
    db.commit()
    db.close()


def rollback_and_close(db: Session):
    """
    回滚并关闭会话
    """
    db.rollback()
    db.close()


class DatabaseManager:
    """
    数据库管理器
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)
    
    def reset_database(self):
        """重置数据库"""
        self.drop_tables()
        self.create_tables()
    
    def execute_sql(self, sql: str):
        """执行SQL语句"""
        session = self.get_session()
        try:
            result = session.execute(sql)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# 创建全局数据库管理器实例
db_manager = DatabaseManager()