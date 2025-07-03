#!/usr/bin/env python3
"""
Test database connection and basic operations.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

async def test_database():
    """Test database connection and basic operations."""
    try:
        print("Testing database connection...")
        
        # Create async engine
        engine = create_async_engine(settings.database.url, echo=True)
        
        # Create session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✓ Basic query successful: {row.test}")
            
            # Check if tables exist
            tables_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            result = await session.execute(tables_query)
            tables = result.fetchall()
            
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table.name}")
            
            # Check users table
            if any(table.name == 'users' for table in tables):
                users_query = text("SELECT COUNT(*) as count FROM users")
                result = await session.execute(users_query)
                count = result.fetchone()
                print(f"✓ Users table has {count.count} records")
            
        await engine.dispose()
        print("✓ Database test completed successfully!")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)