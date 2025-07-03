#!/usr/bin/env python3
"""
Simple database initialization script.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.simple_models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        
        # Create database engine
        engine = create_async_engine(settings.database.url, echo=False)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        logger.info("Database tables created successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def main():
    """Main function."""
    try:
        # Create necessary directories
        settings.create_directories()
        
        # Create database tables
        await create_tables()
        
        logger.info("Database initialization completed!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())