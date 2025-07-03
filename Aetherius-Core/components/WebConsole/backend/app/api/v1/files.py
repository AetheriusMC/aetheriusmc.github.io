"""
File management API endpoints.
"""

import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...utils.security import get_current_user, require_permission
from ...tasks.file import (
    file_cleanup_task, file_archive_task, file_extract_task,
    file_sync_task, file_validation_task
)
from ...tasks.backup import create_backup
from ...websocket.manager import WebSocketManager
from ...websocket.models import create_notification_message

logger = logging.getLogger(__name__)

router = APIRouter()


class FileInfo(BaseModel):
    """File information model."""
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path")
    is_directory: bool = Field(..., description="Is directory flag")
    size: Optional[int] = Field(None, description="File size in bytes")
    modified_time: str = Field(..., description="Last modified timestamp")
    permissions: str = Field(..., description="File permissions")
    owner: Optional[str] = Field(None, description="File owner")
    group: Optional[str] = Field(None, description="File group")


class FileListResponse(BaseModel):
    """File list response model."""
    files: List[FileInfo] = Field(..., description="List of files and directories")
    current_path: str = Field(..., description="Current directory path")
    parent_path: Optional[str] = Field(None, description="Parent directory path")
    total_count: int = Field(..., description="Total number of items")


class FileContent(BaseModel):
    """File content model."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    encoding: str = Field("utf-8", description="File encoding")
    size: int = Field(..., description="Content size in bytes")
    is_binary: bool = Field(False, description="Is binary file")


class FileOperation(BaseModel):
    """File operation request model."""
    operation: str = Field(..., description="Operation type (create, delete, rename, move, copy)")
    source_path: str = Field(..., description="Source file path")
    target_path: Optional[str] = Field(None, description="Target file path")
    is_directory: bool = Field(False, description="Is directory flag")
    overwrite: bool = Field(False, description="Overwrite existing files")


class FileUploadResponse(BaseModel):
    """File upload response model."""
    success: bool = Field(..., description="Upload success status")
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., description="File size")
    path: str = Field(..., description="File path")
    message: str = Field(..., description="Result message")
    timestamp: str = Field(..., description="Upload timestamp")


class BackupRequest(BaseModel):
    """Backup request model."""
    name: Optional[str] = Field(None, description="Backup name")
    description: Optional[str] = Field(None, description="Backup description")
    include_worlds: bool = Field(True, description="Include world data")
    include_plugins: bool = Field(True, description="Include plugin data")
    include_configs: bool = Field(True, description="Include configuration files")
    compression_level: int = Field(6, ge=0, le=9, description="Compression level")


class ArchiveRequest(BaseModel):
    """Archive creation request model."""
    source_path: str = Field(..., description="Source path to archive")
    archive_name: str = Field(..., description="Archive filename")
    archive_type: str = Field("zip", description="Archive type (zip, tar, tar.gz)")
    compression_level: int = Field(6, ge=0, le=9, description="Compression level")


class ExtractRequest(BaseModel):
    """Archive extraction request model."""
    archive_path: str = Field(..., description="Archive file path")
    extract_path: str = Field(..., description="Extraction target path")
    overwrite: bool = Field(False, description="Overwrite existing files")


# Dependency to get WebSocket manager
async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    container = get_container()
    return await container.get_service(WebSocketManager)


@router.get("/list", response_model=FileListResponse)
async def list_files(
    path: str = Query("/", description="Directory path to list"),
    show_hidden: bool = Query(False, description="Show hidden files"),
    current_user: Dict[str, Any] = Depends(require_permission("files.read"))
):
    """
    列出目录下的文件和文件夹。
    
    需要 'files.read' 权限。支持显示隐藏文件选项。
    """
    try:
        logger.info(f"User {current_user['username']} listing files: {path}")
        
        # TODO: Implement actual file listing with security checks
        # For now, return mock data
        
        # Normalize path
        normalized_path = os.path.normpath(path)
        parent_path = os.path.dirname(normalized_path) if normalized_path != "/" else None
        
        # Mock file list
        mock_files = [
            FileInfo(
                name="server.properties",
                path=os.path.join(normalized_path, "server.properties"),
                is_directory=False,
                size=1024,
                modified_time=datetime.now().isoformat(),
                permissions="rw-r--r--",
                owner="minecraft",
                group="minecraft"
            ),
            FileInfo(
                name="plugins",
                path=os.path.join(normalized_path, "plugins"),
                is_directory=True,
                size=None,
                modified_time=datetime.now().isoformat(),
                permissions="rwxr-xr-x",
                owner="minecraft",
                group="minecraft"
            ),
            FileInfo(
                name="worlds",
                path=os.path.join(normalized_path, "worlds"),
                is_directory=True,
                size=None,
                modified_time=datetime.now().isoformat(),
                permissions="rwxr-xr-x",
                owner="minecraft",
                group="minecraft"
            ),
            FileInfo(
                name="logs",
                path=os.path.join(normalized_path, "logs"),
                is_directory=True,
                size=None,
                modified_time=datetime.now().isoformat(),
                permissions="rwxr-xr-x",
                owner="minecraft",
                group="minecraft"
            )
        ]
        
        # Filter hidden files if requested
        if not show_hidden:
            mock_files = [f for f in mock_files if not f.name.startswith('.')]
        
        return FileListResponse(
            files=mock_files,
            current_path=normalized_path,
            parent_path=parent_path,
            total_count=len(mock_files)
        )
        
    except Exception as e:
        logger.error(f"Failed to list files in {path}: {e}")
        raise HTTPException(status_code=500, detail=f"文件列表获取失败: {str(e)}")


@router.get("/content", response_model=FileContent)
async def get_file_content(
    path: str = Query(..., description="File path to read"),
    encoding: str = Query("utf-8", description="File encoding"),
    current_user: Dict[str, Any] = Depends(require_permission("files.read"))
):
    """
    获取文件内容。
    
    需要 'files.read' 权限。支持指定文件编码。
    """
    try:
        logger.info(f"User {current_user['username']} reading file: {path}")
        
        # TODO: Implement actual file reading with security checks
        # Check file size limit, binary detection, etc.
        
        # Mock file content based on file extension
        mock_content = ""
        if path.endswith(".properties"):
            mock_content = "# Minecraft server properties\nserver-port=25565\nmotd=Welcome to Aetherius MC Server\nmax-players=20\n"
        elif path.endswith(".yml") or path.endswith(".yaml"):
            mock_content = "# Configuration file\nversion: 1.0\nsettings:\n  enabled: true\n  debug: false\n"
        elif path.endswith(".json"):
            mock_content = '{\n  "name": "example",\n  "version": "1.0.0",\n  "enabled": true\n}'
        else:
            mock_content = f"# File content for {path}\n# This is a mock file content.\n"
        
        return FileContent(
            path=path,
            content=mock_content,
            encoding=encoding,
            size=len(mock_content.encode(encoding)),
            is_binary=False
        )
        
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")


@router.post("/content")
async def save_file_content(
    content: FileContent,
    background_tasks: BackgroundTasks,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("files.write"))
):
    """
    保存文件内容。
    
    需要 'files.write' 权限。保存后会发送通知。
    """
    try:
        logger.info(f"User {current_user['username']} saving file: {content.path}")
        
        # TODO: Implement actual file saving with security checks
        # Validate file path, check permissions, backup original file, etc.
        
        # Send notification about file save
        notification = create_notification_message(
            title="文件保存",
            message=f"文件 {content.path} 已由 {current_user['username']} 保存",
            level="success",
            duration=5
        )
        background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return {
            "success": True,
            "path": content.path,
            "size": content.size,
            "encoding": content.encoding,
            "message": f"文件 {content.path} 保存成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to save file {content.path}: {e}")
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")


@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("files.backup"))
):
    """
    创建服务器备份。
    
    需要 'files.backup' 权限。支持自定义备份选项。
    """
    try:
        backup_name = request.name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Schedule backup task
        task_result = create_backup.delay(
            backup_name=backup_name,
            description=request.description or f"Manual backup by {current_user['username']}",
            include_worlds=request.include_worlds,
            include_plugins=request.include_plugins,
            include_configs=request.include_configs,
            compression_level=request.compression_level
        )
        
        logger.info(f"User {current_user['username']} started backup: {backup_name}")
        
        return {
            "success": True,
            "message": "备份任务已启动",
            "backup_name": backup_name,
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=f"备份创建失败: {str(e)}")


@router.post("/archive", response_model=Dict[str, Any])
async def create_archive(
    request: ArchiveRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("files.archive"))
):
    """
    创建文件归档。
    
    需要 'files.archive' 权限。支持多种归档格式。
    """
    try:
        # Validate archive type
        valid_types = ["zip", "tar", "tar.gz", "tgz"]
        if request.archive_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的归档类型: {request.archive_type}"
            )
        
        # Schedule archive task
        task_result = file_archive_task.delay(
            source_path=request.source_path,
            archive_path=request.archive_name,
            archive_type=request.archive_type,
            compression_level=request.compression_level
        )
        
        logger.info(f"User {current_user['username']} started archive: {request.source_path} -> {request.archive_name}")
        
        return {
            "success": True,
            "message": "归档任务已启动",
            "archive_name": request.archive_name,
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create archive: {e}")
        raise HTTPException(status_code=500, detail=f"归档创建失败: {str(e)}")


@router.post("/extract", response_model=Dict[str, Any])
async def extract_archive(
    request: ExtractRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("files.archive"))
):
    """
    解压归档文件。
    
    需要 'files.archive' 权限。支持多种归档格式。
    """
    try:
        # Schedule extract task
        task_result = file_extract_task.delay(
            archive_path=request.archive_path,
            extract_path=request.extract_path,
            overwrite=request.overwrite
        )
        
        logger.info(f"User {current_user['username']} started extraction: {request.archive_path} -> {request.extract_path}")
        
        return {
            "success": True,
            "message": "解压任务已启动",
            "archive_path": request.archive_path,
            "extract_path": request.extract_path,
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to extract archive: {e}")
        raise HTTPException(status_code=500, detail=f"归档解压失败: {str(e)}")


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_files(
    background_tasks: BackgroundTasks,
    max_age_days: int = Query(30, ge=1, description="Files older than this will be cleaned"),
    dry_run: bool = Query(False, description="Perform dry run without actual deletion"),
    current_user: Dict[str, Any] = Depends(require_permission("files.manage"))
):
    """
    清理旧文件。
    
    需要 'files.manage' 权限。支持预览模式。
    """
    try:
        # Schedule cleanup task
        cleanup_config = {
            "log_retention_days": max_age_days,
            "backup_retention_days": max_age_days // 2,
            "dry_run": dry_run
        }
        
        task_result = file_cleanup_task.delay(cleanup_config)
        
        logger.info(f"User {current_user['username']} started file cleanup (max_age: {max_age_days} days, dry_run: {dry_run})")
        
        return {
            "success": True,
            "message": "文件清理任务已启动",
            "max_age_days": max_age_days,
            "dry_run": dry_run,
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start file cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"文件清理失败: {str(e)}")


@router.post("/validate", response_model=Dict[str, Any])
async def validate_file(
    background_tasks: BackgroundTasks,
    file_path: str = Query(..., description="File path to validate"),
    validation_type: str = Query("checksum", description="Validation type (checksum, json, archive)"),
    current_user: Dict[str, Any] = Depends(require_permission("files.read"))
):
    """
    验证文件完整性。
    
    需要 'files.read' 权限。支持多种验证类型。
    """
    try:
        # Validate validation type
        valid_types = ["checksum", "json", "archive"]
        if validation_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的验证类型: {validation_type}"
            )
        
        # Schedule validation task
        task_result = file_validation_task.delay(
            file_path=file_path,
            validation_type=validation_type
        )
        
        logger.info(f"User {current_user['username']} started file validation: {file_path} ({validation_type})")
        
        return {
            "success": True,
            "message": "文件验证任务已启动",
            "file_path": file_path,
            "validation_type": validation_type,
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate file: {e}")
        raise HTTPException(status_code=500, detail=f"文件验证失败: {str(e)}")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    path: str = Query("/", description="Target directory path"),
    overwrite: bool = Query(False, description="Overwrite existing file"),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("files.write"))
):
    """
    上传文件。
    
    需要 'files.write' 权限。支持覆盖现有文件选项。
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # TODO: Implement actual file upload with security checks
        # - Validate file type and size
        # - Check target directory permissions
        # - Scan for malicious content
        # - Save file to target location
        
        target_path = f"{path.rstrip('/')}/{file.filename}"
        file_size = 0
        
        # Read file content to get size (mock implementation)
        content = await file.read()
        file_size = len(content)
        
        logger.info(f"User {current_user['username']} uploaded file: {file.filename} ({file_size} bytes) to {path}")
        
        # Send notification about file upload
        notification = create_notification_message(
            title="文件上传",
            message=f"文件 {file.filename} 已由 {current_user['username']} 上传到 {path}",
            level="success",
            duration=5
        )
        background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return FileUploadResponse(
            success=True,
            filename=file.filename,
            size=file_size,
            path=target_path,
            message="文件上传成功",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/download")
async def download_file(
    path: str = Query(..., description="File path to download"),
    current_user: Dict[str, Any] = Depends(require_permission("files.read"))
):
    """
    下载文件。
    
    需要 'files.read' 权限。返回文件内容供下载。
    """
    try:
        logger.info(f"User {current_user['username']} downloading file: {path}")
        
        # TODO: Implement actual file download with security checks
        # - Validate file path
        # - Check file permissions
        # - Stream large files efficiently
        
        # For now, return a placeholder response
        raise HTTPException(status_code=501, detail="文件下载功能正在开发中")
        
        # Example implementation:
        # if not os.path.exists(path):
        #     raise HTTPException(status_code=404, detail="文件不存在")
        # 
        # return FileResponse(
        #     path=path,
        #     filename=os.path.basename(path),
        #     media_type='application/octet-stream'
        # )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.post("/operation", response_model=Dict[str, Any])
async def perform_file_operation(
    operation: FileOperation,
    background_tasks: BackgroundTasks,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("files.write"))
):
    """
    执行文件操作。
    
    需要 'files.write' 权限。支持创建、删除、重命名、移动、复制操作。
    """
    try:
        # Validate operation
        valid_operations = ["create", "delete", "rename", "move", "copy"]
        if operation.operation not in valid_operations:
            raise HTTPException(
                status_code=400,
                detail=f"无效的操作类型: {operation.operation}。支持的操作: {', '.join(valid_operations)}"
            )
        
        # Validate required fields for different operations
        if operation.operation in ["rename", "move", "copy"] and not operation.target_path:
            raise HTTPException(
                status_code=400,
                detail=f"操作 '{operation.operation}' 需要目标路径"
            )
        
        logger.info(f"User {current_user['username']} performing file operation: {operation.operation} on {operation.source_path}")
        
        # TODO: Implement actual file operations with security checks
        # - Validate file paths
        # - Check permissions
        # - Perform atomic operations
        # - Handle errors gracefully
        
        result_message = ""
        if operation.operation == "create":
            if operation.is_directory:
                result_message = f"目录 {operation.source_path} 创建成功"
            else:
                result_message = f"文件 {operation.source_path} 创建成功"
        elif operation.operation == "delete":
            result_message = f"文件/目录 {operation.source_path} 删除成功"
        elif operation.operation == "rename":
            result_message = f"文件/目录已从 {operation.source_path} 重命名为 {operation.target_path}"
        elif operation.operation == "move":
            result_message = f"文件/目录已从 {operation.source_path} 移动到 {operation.target_path}"
        elif operation.operation == "copy":
            result_message = f"文件/目录已从 {operation.source_path} 复制到 {operation.target_path}"
        
        # Send notification about file operation
        notification = create_notification_message(
            title="文件操作",
            message=f"{result_message} (操作员: {current_user['username']})",
            level="success",
            duration=5
        )
        background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return {
            "success": True,
            "operation": operation.operation,
            "source_path": operation.source_path,
            "target_path": operation.target_path,
            "message": result_message,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform file operation: {e}")
        raise HTTPException(status_code=500, detail=f"文件操作失败: {str(e)}")


@router.get("/search")
async def search_files(
    query: str = Query(..., description="Search query"),
    path: str = Query("/", description="Search root path"),
    content_search: bool = Query(False, description="Search file contents")
):
    """Search files."""
    logger.info(f"File search request: '{query}' in {path}")
    
    # TODO: Implement actual file search
    return {
        "query": query,
        "path": path,
        "content_search": content_search,
        "results": [
            {
                "path": "/example.txt",
                "name": "example.txt",
                "match_type": "filename",
                "matches": []
            }
        ],
        "total": 1
    }


@router.get("/permissions")
async def get_file_permissions(
    path: str = Query(..., description="File path")
):
    """Get file permissions."""
    logger.info(f"File permissions request: {path}")
    
    # TODO: Implement actual permissions check
    return {
        "path": path,
        "permissions": {
            "owner": {"read": True, "write": True, "execute": False},
            "group": {"read": True, "write": False, "execute": False},
            "other": {"read": True, "write": False, "execute": False}
        },
        "owner": "minecraft",
        "group": "minecraft"
    }


@router.post("/permissions")
async def set_file_permissions(
    path: str = Query(..., description="File path"),
    permissions: str = Query(..., description="Permissions string (e.g., '755')")
):
    """Set file permissions."""
    logger.info(f"Set file permissions: {path} -> {permissions}")
    
    # TODO: Implement actual permissions setting
    return {
        "success": True,
        "path": path,
        "permissions": permissions,
        "message": "Permissions updated successfully",
        "timestamp": datetime.now().isoformat()
    }