"""Initial database tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('avatar', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Create server_configs table
    op.create_table('server_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('data_type', sa.String(length=20), nullable=False, server_default='string'),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_server_configs_key', 'server_configs', ['key'])
    op.create_index('ix_server_configs_category', 'server_configs', ['category'])

    # Create backup_records table
    op.create_table('backup_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('backup_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('compression', sa.String(length=10), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backup_records_name', 'backup_records', ['name'])
    op.create_index('ix_backup_records_backup_type', 'backup_records', ['backup_type'])
    op.create_index('ix_backup_records_status', 'backup_records', ['status'])
    op.create_index('ix_backup_records_created_at', 'backup_records', ['created_at'])

    # Create console_logs table
    op.create_table('console_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('thread', sa.String(length=50), nullable=True),
        sa.Column('logger_name', sa.String(length=100), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_console_logs_timestamp', 'console_logs', ['timestamp'])
    op.create_index('ix_console_logs_level', 'console_logs', ['level'])
    op.create_index('ix_console_logs_source', 'console_logs', ['source'])

    # Create system_metrics table
    op.create_table('system_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cpu_usage', sa.Float(), nullable=False),
        sa.Column('memory_usage', sa.Float(), nullable=False),
        sa.Column('disk_usage', sa.Float(), nullable=False),
        sa.Column('network_rx', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('network_tx', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('active_connections', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tps', sa.Float(), nullable=True),
        sa.Column('mspt', sa.Float(), nullable=True),
        sa.Column('players_online', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunks_loaded', sa.Integer(), nullable=True),
        sa.Column('entities_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_metrics_timestamp', 'system_metrics', ['timestamp'])

    # Create player_sessions table
    op.create_table('player_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('player_uuid', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=16), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('login_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_duration', sa.Integer(), nullable=True),
        sa.Column('disconnect_reason', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_player_sessions_player_uuid', 'player_sessions', ['player_uuid'])
    op.create_index('ix_player_sessions_username', 'player_sessions', ['username'])
    op.create_index('ix_player_sessions_login_time', 'player_sessions', ['login_time'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='medium'),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('target_user_id', sa.String(), nullable=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_notification_type', 'notifications', ['notification_type'])
    op.create_index('ix_notifications_priority', 'notifications', ['priority'])
    op.create_index('ix_notifications_target_user_id', 'notifications', ['target_user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('prefix', sa.String(length=10), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_ip', sa.String(length=45), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prefix')
    )
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('api_keys')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('player_sessions')
    op.drop_table('system_metrics')
    op.drop_table('console_logs')
    op.drop_table('backup_records')
    op.drop_table('server_configs')
    op.drop_table('users')