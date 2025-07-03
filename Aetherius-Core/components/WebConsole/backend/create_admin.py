#!/usr/bin/env python3
"""
Create admin user and initial data.
"""

import asyncio
import sys
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.simple_models import Base, User, ServerConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin_user(session: AsyncSession):
    """Create default admin user."""
    try:
        # Create admin user
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        admin_user = User(
            id=str(uuid.uuid4()),
            username='admin',
            email='admin@localhost',
            password_hash=admin_password,
            role='admin',
            is_active=True
        )
        
        session.add(admin_user)
        logger.info("Created admin user: admin/admin123")
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise


async def create_default_configs(session: AsyncSession):
    """Create default server configurations."""
    try:
        configs = [
            {
                'key': 'server.name',
                'value': 'Aetherius Server',
                'description': 'Server display name',
                'category': 'server'
            },
            {
                'key': 'server.motd',
                'value': 'Welcome to Aetherius Server!',
                'description': 'Message of the day',
                'category': 'server'
            },
            {
                'key': 'server.max_players',
                'value': '20',
                'description': 'Maximum number of players',
                'category': 'server',
                'data_type': 'integer'
            }
        ]
        
        for config_data in configs:
            config = ServerConfig(
                id=str(uuid.uuid4()),
                **config_data
            )
            session.add(config)
        
        logger.info(f"Created {len(configs)} default configurations")
        
    except Exception as e:
        logger.error(f"Failed to create default configs: {e}")
        raise


async def main():
    """Main function."""
    try:
        logger.info("Creating database and initial data...")
        
        # Create necessary directories
        settings.create_directories()
        
        # Create database engine
        engine = create_async_engine(settings.database.url)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Clear existing tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully!")
        
        # Create session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create admin user
            await create_admin_user(session)
            
            # Create default configurations
            await create_default_configs(session)
            
            # Commit changes
            await session.commit()
        
        await engine.dispose()
        logger.info("Database initialization completed successfully!")
        logger.info("You can now login with username: admin, password: admin123")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())