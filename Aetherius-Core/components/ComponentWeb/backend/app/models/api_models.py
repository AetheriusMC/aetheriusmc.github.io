"""
API Data Models
===============

Pydantic models for API request and response validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Console Models
class ConsoleCommand(BaseModel):
    """Console command request model"""
    command: str = Field(..., min_length=1, max_length=1000, description="Console command to execute")
    
    @validator('command')
    def validate_command(cls, v):
        if not v.strip():
            raise ValueError('Command cannot be empty or whitespace only')
        return v.strip()


class CommandResponse(BaseModel):
    """Console command response model"""
    command: str = Field(..., description="Original command")
    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Command output or error message")
    timestamp: str = Field(..., description="Execution timestamp")
    execution_time: Optional[float] = Field(None, description="Command execution time in seconds")


# Server Status Models
class MemoryInfo(BaseModel):
    """Memory usage information"""
    used: int = Field(..., description="Used memory in MB")
    max: int = Field(..., description="Maximum memory in MB")
    percentage: float = Field(..., ge=0, le=100, description="Memory usage percentage")


class ServerStatus(BaseModel):
    """Server status information"""
    is_running: bool = Field(..., description="Whether server is running")
    uptime: int = Field(..., ge=0, description="Server uptime in seconds")
    version: str = Field(..., description="Server version")
    player_count: int = Field(..., ge=0, description="Current online player count")
    max_players: int = Field(..., ge=0, description="Maximum player capacity")
    tps: float = Field(..., ge=0, description="Ticks per second")
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory_usage: MemoryInfo = Field(..., description="Memory usage information")
    timestamp: str = Field(..., description="Status timestamp")


# Player Models
class Player(BaseModel):
    """Player information model"""
    uuid: str = Field(..., description="Player UUID")
    name: str = Field(..., description="Player name")
    online: bool = Field(..., description="Whether player is currently online")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    ip_address: Optional[str] = Field(None, description="Player IP address")
    game_mode: str = Field("survival", description="Player game mode")
    level: int = Field(0, ge=0, description="Player level")
    experience: int = Field(0, ge=0, description="Player experience points")


class PlayerAction(BaseModel):
    """Player action request model"""
    action: str = Field(..., description="Action to perform")
    reason: Optional[str] = Field(None, description="Reason for the action")
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds (for temporary actions)")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['kick', 'ban', 'unban', 'op', 'deop', 'whitelist', 'unwhitelist']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class PlayerActionResponse(BaseModel):
    """Player action response model"""
    player_uuid: str = Field(..., description="Target player UUID")
    player_name: str = Field(..., description="Target player name")
    action: str = Field(..., description="Action performed")
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Action result message")
    timestamp: str = Field(..., description="Action timestamp")


# File Management Models
class FileInfo(BaseModel):
    """File information model"""
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full file path")
    is_directory: bool = Field(..., description="Whether this is a directory")
    size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    modified_time: str = Field(..., description="Last modified timestamp")
    permissions: str = Field(..., description="File permissions")


class FileContent(BaseModel):
    """File content model"""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    encoding: str = Field("utf-8", description="File encoding")


class FileUpload(BaseModel):
    """File upload model"""
    filename: str = Field(..., description="Upload filename")
    content: bytes = Field(..., description="File content")
    destination_path: str = Field(..., description="Destination path")


# WebSocket Models
class WSConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str = Field(..., description="Connection identifier")
    connection_type: str = Field(..., description="Connection type")
    connected_at: str = Field(..., description="Connection timestamp")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client information")


# Health Check Models
class HealthCheck(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    core_connected: bool = Field(..., description="Whether core is connected")
    websocket_connections: int = Field(..., ge=0, description="Active WebSocket connections")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Health check timestamp")


# Error Response Models
class ErrorDetail(BaseModel):
    """Error detail model"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error summary")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")


# Pagination Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search query")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page")
    limit: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")