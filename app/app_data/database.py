from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from pathlib import Path
import os

dotenv_path = Path("app/.env")
load_dotenv(dotenv_path=dotenv_path)


SQL_DB = os.getenv("POSTGRES_DB")
SQL_USER = os.getenv("POSTGRES_USER")
SQL_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
# SQL_DB = POSTGRES_DB
# SQL_USER = POSTGRES_USER
# SQL_DB_PASSWORD = POSTGRES_PASSWORD
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
SQLALCHEMY_DATABASE_URL = f"postgresql://{SQL_USER}:{SQL_DB_PASSWORD}@db:5432/{SQL_DB}"
# SQLALCHEMY_DATABASE_URL = (
#     f"postgresql://{SQL_USER}:{SQL_DB_PASSWORD}@localhost:5432/{SQL_DB}"
# )

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
