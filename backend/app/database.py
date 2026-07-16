"""Database configuration and session management.

Supports SQLite (dev) and MySQL (production).
DATABASE_URL examples:
- SQLite: sqlite+aiosqlite:///./textbook_qa.db
- MySQL: mysql+aiomysql://user:password@localhost:3306/textbook_qa
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Database URL from environment (default: SQLite)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./textbook_qa.db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    future=True,
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection."""
    await engine.dispose()
