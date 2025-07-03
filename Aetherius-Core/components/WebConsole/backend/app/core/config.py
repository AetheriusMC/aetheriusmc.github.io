"""
Configuration management for WebConsole Backend.

This module provides centralized configuration management using Pydantic Settings,
supporting environment variables, .env files, and default values.
"""

from functools import lru_cache
from typing import List, Optional, Any, Dict
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite+aiosqlite:///./data/webconsole.db",
        description="Database connection URL"
    )
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Maximum pool overflow")
    
    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    cache_db: int = Field(default=1, description="Redis DB for caching")
    celery_broker_db: int = Field(default=2, description="Redis DB for Celery broker")
    celery_backend_db: int = Field(default=3, description="Redis DB for Celery backend")
    default_ttl: int = Field(default=300, description="Default cache TTL in seconds")
    
    model_config = SettingsConfigDict(env_prefix="")
    
    @property
    def cache_url(self) -> str:
        """Get Redis URL for cache."""
        return f"{self.url}/{self.cache_db}"
    
    @property
    def celery_broker_url(self) -> str:
        """Get Redis URL for Celery broker."""
        return f"{self.url}/{self.celery_broker_db}"
    
    @property
    def celery_backend_url(self) -> str:
        """Get Redis URL for Celery backend."""
        return f"{self.url}/{self.celery_backend_db}"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    secret_key: str = Field(
        default="change-me-in-production",
        description="Application secret key"
    )
    jwt_secret_key: str = Field(
        default="change-me-in-production", 
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")
    session_secret_key: str = Field(
        default="change-me-in-production",
        description="Session secret key"
    )
    
    model_config = SettingsConfigDict(env_prefix="")


class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    
    origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods"
    )
    headers: List[str] = Field(
        default=["Content-Type", "Authorization", "X-Requested-With"],
        description="Allowed headers"
    )
    
    model_config = SettingsConfigDict(env_prefix="CORS_")
    
    @field_validator('origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(',')]
        return value
    
    @field_validator('methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, value):
        if isinstance(value, str):
            return [method.strip() for method in value.split(',')]
        return value
    
    @field_validator('headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, value):
        if isinstance(value, str):
            return [header.strip() for header in value.split(',')]
        return value


class WebSocketSettings(BaseSettings):
    """WebSocket configuration settings."""
    
    max_connections: int = Field(default=500, description="Maximum WebSocket connections")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    message_queue_size: int = Field(default=10000, description="Message queue size")
    
    model_config = SettingsConfigDict(env_prefix="WS_")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""
    
    default: str = Field(default="100/minute", description="Default rate limit")
    authenticated: str = Field(default="1000/minute", description="Rate limit for authenticated users")
    burst: int = Field(default=50, description="Burst allowance")
    
    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", description="Log level")
    file: str = Field(default="logs/webconsole.log", description="Log file path")
    rotation: str = Field(default="1 day", description="Log rotation interval")
    retention: str = Field(default="30 days", description="Log retention period")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    model_config = SettingsConfigDict(env_prefix="LOG_")


class MonitoringSettings(BaseSettings):
    """Monitoring configuration settings."""
    
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    opentelemetry_enabled: bool = Field(default=False, description="Enable OpenTelemetry")
    opentelemetry_endpoint: str = Field(default="", description="OpenTelemetry endpoint")
    
    model_config = SettingsConfigDict(env_prefix="")


class FeatureFlags(BaseSettings):
    """Feature flag configuration."""
    
    dashboard: bool = Field(default=True, description="Enable dashboard feature")
    console: bool = Field(default=True, description="Enable console feature")
    player_management: bool = Field(default=True, description="Enable player management")
    file_manager: bool = Field(default=True, description="Enable file manager")
    plugin_management: bool = Field(default=True, description="Enable plugin management")
    backup_system: bool = Field(default=True, description="Enable backup system")
    user_management: bool = Field(default=True, description="Enable user management")
    system_config: bool = Field(default=True, description="Enable system config")
    monitoring: bool = Field(default=True, description="Enable monitoring")
    api_management: bool = Field(default=True, description="Enable API management")
    
    model_config = SettingsConfigDict(env_prefix="FEATURE_")


class AetheriusSettings(BaseSettings):
    """Aetherius Core integration settings."""
    
    core_host: str = Field(default="localhost", description="Aetherius Core host")
    core_port: int = Field(default=25575, description="Aetherius Core port")
    core_timeout: int = Field(default=30, description="Connection timeout in seconds")
    mock_mode: bool = Field(default=False, description="Enable mock mode for development")
    
    model_config = SettingsConfigDict(env_prefix="AETHERIUS_")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application info
    app_name: str = Field(default="Aetherius WebConsole", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    app_description: str = Field(
        default="Enterprise Web Management Console",
        description="Application description"
    )
    debug: bool = Field(default=False, description="Debug mode")
    testing: bool = Field(default=False, description="Testing mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=4, description="Number of workers")
    reload: bool = Field(default=False, description="Auto reload on changes")
    
    # File upload settings
    max_upload_size: int = Field(default=104857600, description="Max upload size in bytes (100MB)")
    allowed_upload_extensions: List[str] = Field(
        default=[".txt", ".yaml", ".yml", ".json", ".properties", ".cfg", ".conf"],
        description="Allowed file extensions for upload"
    )
    upload_directory: str = Field(default="data/uploads", description="Upload directory")
    
    # Backup settings
    backup_directory: str = Field(default="data/backups", description="Backup directory")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    backup_compression: bool = Field(default=True, description="Enable backup compression")
    
    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    websocket: WebSocketSettings = Field(default_factory=WebSocketSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    aetherius: AetheriusSettings = Field(default_factory=AetheriusSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    @field_validator('allowed_upload_extensions', mode='before')
    @classmethod
    def parse_upload_extensions(cls, value):
        if isinstance(value, str):
            return [ext.strip() for ext in value.split(',')]
        return value
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or self.reload
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.testing
    
    def get_database_url(self) -> str:
        """Get the database URL."""
        return self.database.url
    
    def get_redis_cache_url(self) -> str:
        """Get Redis cache URL."""
        return self.redis.cache_url
    
    def create_directories(self) -> None:
        """Create necessary directories."""
        directories = [
            Path(self.upload_directory),
            Path(self.backup_directory),
            Path(self.logging.file).parent,
            Path("data"),
            Path("logs")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.create_directories()
    return settings


# Global settings instance
settings = get_settings()