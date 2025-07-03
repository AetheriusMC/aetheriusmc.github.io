#!/usr/bin/env python3
"""
Simple database initialization script.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import hashlib
import uuid
from datetime import datetime

from app.core.config import settings

async def create_tables():
    """Create all tables directly."""
    
    engine = create_async_engine(settings.database.url, echo=True)
    
    async with engine.begin() as conn:
        # Create users table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user' NOT NULL,
                avatar TEXT,
                is_active BOOLEAN DEFAULT 1 NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                last_login TIMESTAMP
            )
        """))
        
        # Create server_configs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS server_configs (
                id TEXT PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                category TEXT,
                data_type TEXT DEFAULT 'string' NOT NULL,
                is_encrypted BOOLEAN DEFAULT 0 NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """))
        
        # Create console_logs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS console_logs (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT,
                thread TEXT,
                logger_name TEXT,
                stack_trace TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """))
        
        # Create system_metrics table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                cpu_usage REAL NOT NULL,
                memory_usage REAL NOT NULL,
                disk_usage REAL NOT NULL,
                network_rx INTEGER DEFAULT 0 NOT NULL,
                network_tx INTEGER DEFAULT 0 NOT NULL,
                active_connections INTEGER DEFAULT 0 NOT NULL,
                tps REAL,
                mspt REAL,
                players_online INTEGER DEFAULT 0 NOT NULL,
                chunks_loaded INTEGER,
                entities_count INTEGER
            )
        """))
        
        # Create notifications table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                priority TEXT DEFAULT 'medium' NOT NULL,
                sender_id TEXT,
                target_user_id TEXT,
                is_global BOOLEAN DEFAULT 0 NOT NULL,
                is_read BOOLEAN DEFAULT 0 NOT NULL,
                read_at TIMESTAMP,
                expires_at TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (target_user_id) REFERENCES users(id)
            )
        """))
        
        print("✓ Created all tables successfully")
        
        # Insert default admin user
        admin_id = str(uuid.uuid4())
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        current_time = datetime.utcnow().isoformat()
        
        await conn.execute(text("""
            INSERT OR IGNORE INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
            VALUES (:id, :username, :email, :password_hash, :role, :is_active, :created_at, :updated_at)
        """), {
            'id': admin_id,
            'username': 'admin',
            'email': 'admin@localhost',
            'password_hash': admin_password,
            'role': 'admin',
            'is_active': True,
            'created_at': current_time,
            'updated_at': current_time
        })
        
        print("✓ Created default admin user (username: admin, password: admin123)")
        
        # Insert some default configurations
        configs = [
            {
                'id': str(uuid.uuid4()),
                'key': 'server.name',
                'value': 'Aetherius Server',
                'description': 'Server display name',
                'category': 'server',
                'data_type': 'string',
                'is_encrypted': False,
                'created_at': current_time,
                'updated_at': current_time
            },
            {
                'id': str(uuid.uuid4()),
                'key': 'server.motd',
                'value': 'Welcome to Aetherius Server!',
                'description': 'Message of the day',
                'category': 'server',
                'data_type': 'string',
                'is_encrypted': False,
                'created_at': current_time,
                'updated_at': current_time
            }
        ]
        
        for config in configs:
            await conn.execute(text("""
                INSERT OR IGNORE INTO server_configs (id, key, value, description, category, data_type, is_encrypted, created_at, updated_at)
                VALUES (:id, :key, :value, :description, :category, :data_type, :is_encrypted, :created_at, :updated_at)
            """), config)
        
        print("✓ Inserted default configurations")
    
    await engine.dispose()
    print("✓ Database initialization completed successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())