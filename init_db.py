"""
Database initialization script
Run this once to create the database tables
"""
from database import Base, engine
import models

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
