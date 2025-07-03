"""Seed initial data

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, DateTime, Boolean, Text
import hashlib
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create temporary table definitions for data insertion
    users_table = table('users',
        column('id', String),
        column('username', String),
        column('email', String),
        column('password_hash', String),
        column('role', String),
        column('is_active', Boolean),
        column('created_at', DateTime),
        column('updated_at', DateTime)
    )
    
    server_configs_table = table('server_configs',
        column('id', String),
        column('key', String),
        column('value', Text),
        column('description', Text),
        column('category', String),
        column('data_type', String),
        column('created_at', DateTime),
        column('updated_at', DateTime)
    )
    
    # Create default admin user
    admin_id = str(uuid.uuid4())
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()  # Default password
    current_time = datetime.utcnow()
    
    op.bulk_insert(users_table, [
        {
            'id': admin_id,
            'username': 'admin',
            'email': 'admin@localhost',
            'password_hash': admin_password,
            'role': 'admin',
            'is_active': True,
            'created_at': current_time,
            'updated_at': current_time
        }
    ])
    
    # Insert default server configurations
    default_configs = [
        # Server Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'server.name',
            'value': 'Aetherius Server',
            'description': 'Server display name',
            'category': 'server',
            'data_type': 'string',
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
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'server.max_players',
            'value': '20',
            'description': 'Maximum number of players',
            'category': 'server',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'server.difficulty',
            'value': 'normal',
            'description': 'Server difficulty level',
            'category': 'server',
            'data_type': 'string',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'server.gamemode',
            'value': 'survival',
            'description': 'Default game mode',
            'category': 'server',
            'data_type': 'string',
            'created_at': current_time,
            'updated_at': current_time
        },
        
        # Security Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'security.whitelist_enabled',
            'value': 'false',
            'description': 'Enable whitelist mode',
            'category': 'security',
            'data_type': 'boolean',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'security.online_mode',
            'value': 'true',
            'description': 'Enable online mode authentication',
            'category': 'security',
            'data_type': 'boolean',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'security.spawn_protection',
            'value': '16',
            'description': 'Spawn protection radius',
            'category': 'security',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        
        # Performance Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'performance.view_distance',
            'value': '10',
            'description': 'Server view distance',
            'category': 'performance',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'performance.simulation_distance',
            'value': '10',
            'description': 'Simulation distance for chunks',
            'category': 'performance',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'performance.max_tick_time',
            'value': '60000',
            'description': 'Maximum tick time in milliseconds',
            'category': 'performance',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        
        # Backup Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'backup.auto_backup_enabled',
            'value': 'true',
            'description': 'Enable automatic backups',
            'category': 'backup',
            'data_type': 'boolean',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'backup.backup_interval',
            'value': '24',
            'description': 'Backup interval in hours',
            'category': 'backup',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'backup.retention_days',
            'value': '7',
            'description': 'Number of days to keep backups',
            'category': 'backup',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'backup.compression_enabled',
            'value': 'true',
            'description': 'Enable backup compression',
            'category': 'backup',
            'data_type': 'boolean',
            'created_at': current_time,
            'updated_at': current_time
        },
        
        # Monitoring Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'monitoring.metrics_enabled',
            'value': 'true',
            'description': 'Enable system metrics collection',
            'category': 'monitoring',
            'data_type': 'boolean',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'monitoring.metrics_interval',
            'value': '60',
            'description': 'Metrics collection interval in seconds',
            'category': 'monitoring',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'monitoring.alert_cpu_threshold',
            'value': '85.0',
            'description': 'CPU usage alert threshold percentage',
            'category': 'monitoring',
            'data_type': 'float',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'monitoring.alert_memory_threshold',
            'value': '90.0',
            'description': 'Memory usage alert threshold percentage',
            'category': 'monitoring',
            'data_type': 'float',
            'created_at': current_time,
            'updated_at': current_time
        },
        
        # Console Settings
        {
            'id': str(uuid.uuid4()),
            'key': 'console.log_level',
            'value': 'info',
            'description': 'Console logging level',
            'category': 'console',
            'data_type': 'string',
            'created_at': current_time,
            'updated_at': current_time
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'console.log_retention_days',
            'value': '30',
            'description': 'Number of days to keep console logs',
            'category': 'console',
            'data_type': 'integer',
            'created_at': current_time,
            'updated_at': current_time
        }
    ]
    
    op.bulk_insert(server_configs_table, default_configs)


def downgrade() -> None:
    # Remove default configurations
    op.execute("DELETE FROM server_configs WHERE key LIKE 'server.%' OR key LIKE 'security.%' OR key LIKE 'performance.%' OR key LIKE 'backup.%' OR key LIKE 'monitoring.%' OR key LIKE 'console.%'")
    
    # Remove default admin user
    op.execute("DELETE FROM users WHERE username = 'admin' AND email = 'admin@localhost'")