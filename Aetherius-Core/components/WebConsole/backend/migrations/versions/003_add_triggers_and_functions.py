"""Add database triggers and functions

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at columns
    op.execute("""
        CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_server_configs_updated_at 
        BEFORE UPDATE ON server_configs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_api_keys_updated_at 
        BEFORE UPDATE ON api_keys
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create function to clean up old records
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_records()
        RETURNS void AS $$
        BEGIN
            -- Clean up console logs older than 30 days
            DELETE FROM console_logs 
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
            
            -- Clean up system metrics older than 90 days
            DELETE FROM system_metrics 
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';
            
            -- Clean up player sessions older than 1 year
            DELETE FROM player_sessions 
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 year';
            
            -- Clean up audit logs older than 1 year
            DELETE FROM audit_logs 
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
            
            -- Clean up read notifications older than 30 days
            DELETE FROM notifications 
            WHERE is_read = true AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
            
            -- Clean up expired notifications
            DELETE FROM notifications 
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create function to calculate session duration
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_session_duration()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.logout_time IS NOT NULL AND NEW.login_time IS NOT NULL THEN
                NEW.session_duration = EXTRACT(EPOCH FROM (NEW.logout_time - NEW.login_time))::INTEGER;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create trigger for session duration calculation
    op.execute("""
        CREATE TRIGGER calculate_player_session_duration
        BEFORE INSERT OR UPDATE ON player_sessions
        FOR EACH ROW EXECUTE FUNCTION calculate_session_duration();
    """)
    
    # Create function to log audit events
    op.execute("""
        CREATE OR REPLACE FUNCTION log_user_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                -- Log user updates
                IF OLD.is_active != NEW.is_active THEN
                    INSERT INTO audit_logs (
                        id, timestamp, user_id, username, action, resource_type, resource_id,
                        details, success
                    ) VALUES (
                        gen_random_uuid()::text,
                        CURRENT_TIMESTAMP,
                        NEW.id,
                        NEW.username,
                        CASE WHEN NEW.is_active THEN 'user_activated' ELSE 'user_deactivated' END,
                        'user',
                        NEW.id,
                        jsonb_build_object(
                            'old_status', OLD.is_active,
                            'new_status', NEW.is_active
                        ),
                        true
                    );
                END IF;
                
                IF OLD.role != NEW.role THEN
                    INSERT INTO audit_logs (
                        id, timestamp, user_id, username, action, resource_type, resource_id,
                        details, success
                    ) VALUES (
                        gen_random_uuid()::text,
                        CURRENT_TIMESTAMP,
                        NEW.id,
                        NEW.username,
                        'user_role_changed',
                        'user',
                        NEW.id,
                        jsonb_build_object(
                            'old_role', OLD.role,
                            'new_role', NEW.role
                        ),
                        true
                    );
                END IF;
                
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                -- Log user creation
                INSERT INTO audit_logs (
                    id, timestamp, user_id, username, action, resource_type, resource_id,
                    details, success
                ) VALUES (
                    gen_random_uuid()::text,
                    CURRENT_TIMESTAMP,
                    NEW.id,
                    NEW.username,
                    'user_created',
                    'user',
                    NEW.id,
                    jsonb_build_object(
                        'role', NEW.role,
                        'email', NEW.email
                    ),
                    true
                );
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create trigger for user audit logging
    op.execute("""
        CREATE TRIGGER log_user_changes_trigger
        AFTER INSERT OR UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION log_user_changes();
    """)
    
    # Create function for notification cleanup
    op.execute("""
        CREATE OR REPLACE FUNCTION mark_notification_read()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.is_read = true AND OLD.is_read = false THEN
                NEW.read_at = CURRENT_TIMESTAMP;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create trigger for notification read timestamp
    op.execute("""
        CREATE TRIGGER update_notification_read_at
        BEFORE UPDATE ON notifications
        FOR EACH ROW EXECUTE FUNCTION mark_notification_read();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_notification_read_at ON notifications;")
    op.execute("DROP TRIGGER IF EXISTS log_user_changes_trigger ON users;")
    op.execute("DROP TRIGGER IF EXISTS calculate_player_session_duration ON player_sessions;")
    op.execute("DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;")
    op.execute("DROP TRIGGER IF EXISTS update_server_configs_updated_at ON server_configs;")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS mark_notification_read();")
    op.execute("DROP FUNCTION IF EXISTS log_user_changes();")
    op.execute("DROP FUNCTION IF EXISTS calculate_session_duration();")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_records();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")