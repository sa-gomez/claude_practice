import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://todouser:todopass@localhost:5432/todos_db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL statements
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """Dependency function for FastAPI route injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
