"""Add additional indexes and constraints

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add compound indexes for better query performance
    op.create_index('ix_console_logs_timestamp_level', 'console_logs', ['timestamp', 'level'])
    op.create_index('ix_system_metrics_timestamp_cpu', 'system_metrics', ['timestamp', 'cpu_usage'])
    op.create_index('ix_player_sessions_player_logout', 'player_sessions', ['player_uuid', 'logout_time'])
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_notifications_user_read', 'notifications', ['target_user_id', 'is_read'])
    op.create_index('ix_backup_records_type_status', 'backup_records', ['backup_type', 'status'])
    
    # Add partial indexes for active records
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_users_active 
        ON users (username) 
        WHERE is_active = true
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_api_keys_active 
        ON api_keys (key_hash) 
        WHERE is_active = true
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_notifications_unread 
        ON notifications (created_at DESC) 
        WHERE is_read = false
    """)
    
    # Add check constraints
    op.create_check_constraint(
        'ck_users_role',
        'users',
        "role IN ('admin', 'moderator', 'user')"
    )
    
    op.create_check_constraint(
        'ck_backup_records_type',
        'backup_records',
        "backup_type IN ('full', 'incremental', 'world', 'plugins', 'configs')"
    )
    
    op.create_check_constraint(
        'ck_backup_records_status',
        'backup_records',
        "status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')"
    )
    
    op.create_check_constraint(
        'ck_console_logs_level',
        'console_logs',
        "level IN ('debug', 'info', 'warning', 'error', 'critical')"
    )
    
    op.create_check_constraint(
        'ck_notifications_type',
        'notifications',
        "notification_type IN ('system', 'security', 'player', 'server', 'maintenance', 'alert', 'info', 'warning', 'error')"
    )
    
    op.create_check_constraint(
        'ck_notifications_priority',
        'notifications',
        "priority IN ('low', 'medium', 'high', 'critical')"
    )
    
    op.create_check_constraint(
        'ck_system_metrics_ranges',
        'system_metrics',
        "cpu_usage >= 0 AND cpu_usage <= 100 AND memory_usage >= 0 AND memory_usage <= 100 AND disk_usage >= 0 AND disk_usage <= 100"
    )


def downgrade() -> None:
    # Drop check constraints
    op.drop_constraint('ck_system_metrics_ranges', 'system_metrics', type_='check')
    op.drop_constraint('ck_notifications_priority', 'notifications', type_='check')
    op.drop_constraint('ck_notifications_type', 'notifications', type_='check')
    op.drop_constraint('ck_console_logs_level', 'console_logs', type_='check')
    op.drop_constraint('ck_backup_records_status', 'backup_records', type_='check')
    op.drop_constraint('ck_backup_records_type', 'backup_records', type_='check')
    op.drop_constraint('ck_users_role', 'users', type_='check')
    
    # Drop partial indexes
    op.drop_index('ix_notifications_unread', 'notifications')
    op.drop_index('ix_api_keys_active', 'api_keys')
    op.drop_index('ix_users_active', 'users')
    
    # Drop compound indexes
    op.drop_index('ix_backup_records_type_status', 'backup_records')
    op.drop_index('ix_notifications_user_read', 'notifications')
    op.drop_index('ix_audit_logs_user_timestamp', 'audit_logs')
    op.drop_index('ix_player_sessions_player_logout', 'player_sessions')
    op.drop_index('ix_system_metrics_timestamp_cpu', 'system_metrics')
    op.drop_index('ix_console_logs_timestamp_level', 'console_logs')