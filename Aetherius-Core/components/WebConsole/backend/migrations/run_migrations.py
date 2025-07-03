#!/usr/bin/env python3
"""
Database migration runner script for WebConsole.
This script handles database initialization and migrations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import logging

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database_connection():
    """Check if database is accessible."""
    try:
        engine = create_async_engine(settings.database.url)
        async with engine.connect() as conn:
            # Just execute the query without fetching results
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def create_database_if_not_exists():
    """Create database if it doesn't exist."""
    try:
        # Extract database name from URL
        db_url = settings.database.url
        if 'postgresql' in db_url:
            # For PostgreSQL, connect to 'postgres' database to create the target database
            parts = db_url.split('/')
            db_name = parts[-1].split('?')[0]  # Remove query parameters
            admin_url = '/'.join(parts[:-1]) + '/postgres'
            
            engine = create_async_engine(admin_url)
            async with engine.connect() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                exists = result.fetchone()
                
                if not exists:
                    # Create database
                    await conn.execute(text("COMMIT"))  # End transaction
                    await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Created database: {db_name}")
                else:
                    logger.info(f"Database already exists: {db_name}")
            
            await engine.dispose()
        else:
            # For SQLite, the database file will be created automatically
            logger.info("Using SQLite - database will be created automatically")
            
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


def run_migrations():
    """Run database migrations."""
    try:
        # Get the directory containing this script
        migrations_dir = Path(__file__).parent
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def generate_migration(message: str):
    """Generate a new migration file."""
    try:
        migrations_dir = Path(__file__).parent
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
        
        logger.info(f"Generating migration: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        logger.info("Migration file generated successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate migration: {e}")
        raise


def show_current_revision():
    """Show current database revision."""
    try:
        migrations_dir = Path(__file__).parent
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
        
        command.current(alembic_cfg)
        
    except Exception as e:
        logger.error(f"Failed to show current revision: {e}")
        raise


def show_migration_history():
    """Show migration history."""
    try:
        migrations_dir = Path(__file__).parent
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
        
        command.history(alembic_cfg)
        
    except Exception as e:
        logger.error(f"Failed to show migration history: {e}")
        raise


async def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WebConsole Database Migration Tool")
    parser.add_argument(
        "command",
        choices=["init", "migrate", "generate", "current", "history"],
        help="Migration command to execute"
    )
    parser.add_argument(
        "--message", "-m",
        help="Migration message (required for generate command)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "init":
            logger.info("Initializing database...")
            await create_database_if_not_exists()
            
            # Check connection
            if not await check_database_connection():
                logger.error("Database connection failed after initialization")
                sys.exit(1)
                
            # Run initial migrations
            run_migrations()
            logger.info("Database initialization completed")
            
        elif args.command == "migrate":
            logger.info("Running migrations...")
            if not await check_database_connection():
                logger.error("Database connection failed")
                sys.exit(1)
            run_migrations()
            
        elif args.command == "generate":
            if not args.message:
                logger.error("Migration message is required for generate command")
                sys.exit(1)
            generate_migration(args.message)
            
        elif args.command == "current":
            show_current_revision()
            
        elif args.command == "history":
            show_migration_history()
            
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())