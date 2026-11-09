import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Base class for all database models
class Base(DeclarativeBase):
    pass


# Read MySQL credentials from .env
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE", "hawker_safety_auditor")
)

# Create MySQL engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)


# Create database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


def init_db():
    """Create database tables if they do not already exist."""

    # Import models so SQLAlchemy knows which tables to create
    from database import models

    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully.")