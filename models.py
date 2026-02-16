from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Todo(Base):
    """SQLAlchemy model for Todo table"""
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
