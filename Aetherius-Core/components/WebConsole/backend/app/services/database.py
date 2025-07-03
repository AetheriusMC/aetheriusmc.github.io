"""
Database service implementation.
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from ..core.config import settings
from ..core.container import singleton
from ..models.base import Base

logger = logging.getLogger(__name__)


@singleton
class DatabaseService:
    """Database service for managing SQLAlchemy async sessions."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        try:
            # Create async engine
            engine_kwargs = {
                "echo": settings.database.echo,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
            
            # SQLite specific configuration
            if settings.database.url.startswith("sqlite"):
                engine_kwargs.update({
                    "poolclass": StaticPool,
                    "connect_args": {
                        "check_same_thread": False,
                        "timeout": 20
                    }
                })
            else:
                # PostgreSQL/MySQL configuration
                engine_kwargs.update({
                    "pool_size": settings.database.pool_size,
                    "max_overflow": settings.database.max_overflow
                })
            
            self.engine = create_async_engine(
                settings.database.url,
                **engine_kwargs
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.initialized = True
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def dispose(self) -> None:
        """Dispose database engine."""
        if self.engine:
            await self.engine.dispose()
        self.initialized = False
        logger.info("Database service disposed")
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self.initialized:
            raise RuntimeError("Database service not initialized")
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self.initialized:
            raise RuntimeError("Database service not initialized")
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager."""
        if not self.initialized:
            raise RuntimeError("Database service not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_session(self) -> AsyncSession:
        """Get database session (manual management)."""
        if not self.initialized:
            raise RuntimeError("Database service not initialized")
        
        return self.session_factory()
    
    async def health_check(self) -> bool:
        """Check database health."""
        if not self.initialized:
            return False
        
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Database session dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    from ..core.container import get_container
    
    container = get_container()
    db_service = await container.get_service(DatabaseService)
    
    async with db_service.session() as session:
        yield session