"""
File Management API Routes
==========================

API endpoints for file and directory management operations.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import aiofiles
import mimetypes
import shutil
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator

from ..models.api_models import FileInfo, FileContent, ErrorResponse
from ..core.api import CoreAPI


router = APIRouter()


class FileListRequest(BaseModel):
    """File list request parameters"""
    path: str = Field(".", description="Directory path to list")
    show_hidden: bool = Field(False, description="Whether to show hidden files")
    recursive: bool = Field(False, description="Whether to list recursively")


class FileOperationRequest(BaseModel):
    """File operation request"""
    source_path: str = Field(..., description="Source file/directory path")
    destination_path: Optional[str] = Field(None, description="Destination path (for move/copy)")
    operation: str = Field(..., description="Operation type")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed = ['delete', 'move', 'copy', 'create_directory']
        if v not in allowed:
            raise ValueError(f'Operation must be one of: {", ".join(allowed)}')
        return v


class FileSearchRequest(BaseModel):
    """File search request"""
    path: str = Field(".", description="Search root path")
    query: str = Field(..., min_length=1, description="Search query")
    file_types: Optional[List[str]] = Field(None, description="File extensions to filter")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum results")


class FileEditRequest(BaseModel):
    """File edit request"""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="New file content")
    encoding: str = Field("utf-8", description="File encoding")
    backup: bool = Field(True, description="Create backup before editing")


async def get_core_api(request: Request) -> CoreAPI:
    """Get CoreAPI instance from request state"""
    if hasattr(request.app.state, 'core'):
        return CoreAPI(request.app.state.core)
    raise HTTPException(status_code=503, detail="Core API not available")


def normalize_path(path: str) -> Path:
    """Normalize and validate file path"""
    # Remove leading slash and resolve relative paths
    if path.startswith('/'):
        path = path[1:]
    
    # Convert to Path object and resolve
    resolved_path = Path('.') / path
    resolved_path = resolved_path.resolve()
    
    return resolved_path


def is_safe_path(path: Path, base_path: Path = Path('.').resolve()) -> bool:
    """Check if path is safe (within allowed directory)"""
    try:
        # Ensure path is within base directory
        resolved_path = path.resolve()
        return str(resolved_path).startswith(str(base_path))
    except (OSError, ValueError):
        return False


def get_file_info(path: Path) -> FileInfo:
    """Get file information"""
    try:
        stat = path.stat()
        return FileInfo(
            name=path.name,
            path=str(path),
            is_directory=path.is_dir(),
            size=stat.st_size if path.is_file() else None,
            modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            permissions=oct(stat.st_mode)[-3:]
        )
    except OSError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")


@router.get("/files/list", response_model=Dict[str, Any])
async def list_files(
    path: str = Query(".", description="Directory path"),
    show_hidden: bool = Query(False, description="Show hidden files"),
    recursive: bool = Query(False, description="List recursively"),
    core_api: CoreAPI = Depends(get_core_api)
):
    """List files and directories"""
    
    try:
        # Normalize and validate path
        target_path = normalize_path(path)
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not target_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        files = []
        directories = []
        
        try:
            # List directory contents
            for item in target_path.iterdir():
                # Skip hidden files if not requested
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    file_info = get_file_info(item)
                    if file_info.is_directory:
                        directories.append(file_info)
                    else:
                        files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
            
            # Sort results
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            return {
                "success": True,
                "path": str(target_path),
                "parent_path": str(target_path.parent) if target_path.parent != target_path else None,
                "directories": directories,
                "files": files,
                "total_directories": len(directories),
                "total_files": len(files)
            }
            
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")


@router.get("/files/content", response_model=Dict[str, Any])
async def get_file_content(
    path: str = Query(..., description="File path"),
    encoding: str = Query("utf-8", description="File encoding"),
    core_api: CoreAPI = Depends(get_core_api)
):
    """Get file content"""
    
    try:
        # Normalize and validate path
        target_path = normalize_path(path)
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if target_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")
        
        # Check file size (limit to 10MB for text editing)
        file_size = target_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large for editing (max 10MB)")
        
        # Read file content
        try:
            async with aiofiles.open(target_path, 'r', encoding=encoding) as f:
                content = await f.read()
            
            file_info = get_file_info(target_path)
            
            return {
                "success": True,
                "file_info": file_info,
                "content": content,
                "encoding": encoding,
                "size": file_size,
                "lines": len(content.splitlines())
            }
            
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail=f"Cannot decode file with {encoding} encoding")
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/files/save", response_model=Dict[str, Any])
async def save_file_content(
    request: FileEditRequest,
    core_api: CoreAPI = Depends(get_core_api)
):
    """Save file content"""
    
    try:
        # Normalize and validate path
        target_path = normalize_path(request.path)
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        # Create backup if requested and file exists
        backup_path = None
        if request.backup and target_path.exists():
            backup_path = target_path.with_suffix(target_path.suffix + '.backup')
            shutil.copy2(target_path, backup_path)
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        try:
            async with aiofiles.open(target_path, 'w', encoding=request.encoding) as f:
                await f.write(request.content)
            
            file_info = get_file_info(target_path)
            
            return {
                "success": True,
                "message": "File saved successfully",
                "file_info": file_info,
                "backup_created": backup_path is not None,
                "backup_path": str(backup_path) if backup_path else None
            }
            
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        except UnicodeEncodeError:
            raise HTTPException(status_code=400, detail=f"Cannot encode content with {request.encoding} encoding")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@router.post("/files/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    destination_path: str = Form(...),
    overwrite: bool = Form(False),
    core_api: CoreAPI = Depends(get_core_api)
):
    """Upload file"""
    
    try:
        # Normalize and validate destination path
        target_path = normalize_path(destination_path) / file.filename
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        # Check if file already exists
        if target_path.exists() and not overwrite:
            raise HTTPException(status_code=409, detail="File already exists")
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        try:
            async with aiofiles.open(target_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            file_info = get_file_info(target_path)
            
            return {
                "success": True,
                "message": "File uploaded successfully",
                "file_info": file_info,
                "uploaded_size": len(content)
            }
            
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/files/download")
async def download_file(
    path: str = Query(..., description="File path"),
    core_api: CoreAPI = Depends(get_core_api)
):
    """Download file"""
    
    try:
        # Normalize and validate path
        target_path = normalize_path(path)
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if target_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot download directory")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(target_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        return FileResponse(
            path=target_path,
            filename=target_path.name,
            media_type=mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.post("/files/operation", response_model=Dict[str, Any])
async def file_operation(
    request: FileOperationRequest,
    core_api: CoreAPI = Depends(get_core_api)
):
    """Perform file operation (delete, move, copy, create directory)"""
    
    try:
        # Normalize and validate source path
        source_path = normalize_path(request.source_path)
        if not is_safe_path(source_path):
            raise HTTPException(status_code=403, detail="Access denied: Source path outside allowed directory")
        
        if request.operation == 'create_directory':
            # Create directory
            source_path.mkdir(parents=True, exist_ok=True)
            file_info = get_file_info(source_path)
            return {
                "success": True,
                "message": "Directory created successfully",
                "operation": request.operation,
                "file_info": file_info
            }
        
        # For other operations, source must exist
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source file/directory not found")
        
        if request.operation == 'delete':
            # Delete file or directory
            if source_path.is_dir():
                shutil.rmtree(source_path)
            else:
                source_path.unlink()
            
            return {
                "success": True,
                "message": f"{'Directory' if source_path.is_dir() else 'File'} deleted successfully",
                "operation": request.operation,
                "path": str(source_path)
            }
        
        elif request.operation in ['move', 'copy']:
            if not request.destination_path:
                raise HTTPException(status_code=400, detail="Destination path required for move/copy operations")
            
            # Normalize and validate destination path
            dest_path = normalize_path(request.destination_path)
            if not is_safe_path(dest_path):
                raise HTTPException(status_code=403, detail="Access denied: Destination path outside allowed directory")
            
            # Ensure destination parent exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if request.operation == 'move':
                shutil.move(str(source_path), str(dest_path))
                message = "File/directory moved successfully"
            else:  # copy
                if source_path.is_dir():
                    shutil.copytree(str(source_path), str(dest_path))
                else:
                    shutil.copy2(str(source_path), str(dest_path))
                message = "File/directory copied successfully"
            
            file_info = get_file_info(dest_path)
            return {
                "success": True,
                "message": message,
                "operation": request.operation,
                "source_path": str(source_path),
                "destination_path": str(dest_path),
                "file_info": file_info
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
            
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@router.post("/files/search", response_model=Dict[str, Any])
async def search_files(
    request: FileSearchRequest,
    core_api: CoreAPI = Depends(get_core_api)
):
    """Search files and directories"""
    
    try:
        # Normalize and validate search path
        search_path = normalize_path(request.path)
        if not is_safe_path(search_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        if not search_path.exists():
            raise HTTPException(status_code=404, detail="Search path not found")
        
        if not search_path.is_dir():
            raise HTTPException(status_code=400, detail="Search path must be a directory")
        
        results = []
        query_lower = request.query.lower()
        
        # Search files recursively
        def search_recursive(path: Path, depth: int = 0):
            if depth > 10:  # Limit recursion depth
                return
            
            try:
                for item in path.iterdir():
                    if len(results) >= request.max_results:
                        break
                    
                    # Skip hidden files
                    if item.name.startswith('.'):
                        continue
                    
                    # Check if name matches query
                    if query_lower in item.name.lower():
                        # Filter by file type if specified
                        if request.file_types and item.is_file():
                            file_ext = item.suffix.lower()
                            if file_ext not in [f'.{ext.lower()}' for ext in request.file_types]:
                                continue
                        
                        try:
                            file_info = get_file_info(item)
                            results.append(file_info)
                        except (OSError, PermissionError):
                            continue
                    
                    # Recurse into directories
                    if item.is_dir():
                        search_recursive(item, depth + 1)
                        
            except (OSError, PermissionError):
                pass
        
        search_recursive(search_path)
        
        return {
            "success": True,
            "query": request.query,
            "search_path": str(search_path),
            "results": results,
            "total_results": len(results),
            "max_results_reached": len(results) >= request.max_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/files/info", response_model=Dict[str, Any])
async def get_file_info_endpoint(
    path: str = Query(..., description="File path"),
    core_api: CoreAPI = Depends(get_core_api)
):
    """Get detailed file information"""
    
    try:
        # Normalize and validate path
        target_path = normalize_path(path)
        if not is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = get_file_info(target_path)
        
        # Additional info for files
        additional_info = {}
        if target_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(target_path))
            additional_info.update({
                "mime_type": mime_type or 'application/octet-stream',
                "readable": os.access(target_path, os.R_OK),
                "writable": os.access(target_path, os.W_OK),
                "executable": os.access(target_path, os.X_OK)
            })
        
        return {
            "success": True,
            "file_info": file_info,
            "additional_info": additional_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")