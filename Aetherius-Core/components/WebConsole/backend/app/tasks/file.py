"""
File management and processing tasks.
"""

import asyncio
import logging
import os
import shutil
import zipfile
import tarfile
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from celery import Task

from .base import BaseTask
from ..core.config import settings
from ..core.container import get_container
from ..websocket.manager import WebSocketManager
from ..websocket.models import create_notification_message

logger = logging.getLogger(__name__)


class FileTask(BaseTask):
    """Base class for file management tasks."""
    pass


class FileCleanupTask(FileTask):
    """Task to clean up temporary and old files."""
    
    def run(self, cleanup_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Clean up files based on configuration."""
        try:
            return self._cleanup_files(cleanup_config or {})
        except Exception as e:
            logger.error(f"File cleanup task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _cleanup_files(self, cleanup_config: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old and temporary files."""
        try:
            cleanup_summary = {
                "timestamp": datetime.now().isoformat(),
                "cleaned_directories": [],
                "deleted_files": [],
                "freed_space_mb": 0,
                "errors": []
            }
            
            # Default cleanup configuration
            default_config = {
                "temp_directories": ["/tmp", str(Path.home() / "tmp")],
                "log_retention_days": 30,
                "backup_retention_days": 7,
                "cache_retention_hours": 24
            }
            
            config = {**default_config, **cleanup_config}
            
            # Clean temporary directories
            for temp_dir in config.get("temp_directories", []):
                if os.path.exists(temp_dir):
                    try:
                        cleaned = self._clean_directory(temp_dir, max_age_hours=1)
                        cleanup_summary["cleaned_directories"].append({
                            "directory": temp_dir,
                            "files_deleted": len(cleaned),
                            "files": cleaned
                        })
                        cleanup_summary["deleted_files"].extend(cleaned)
                    except Exception as e:
                        cleanup_summary["errors"].append(f"Failed to clean {temp_dir}: {e}")
            
            # Clean old log files
            log_dir = settings.logging.directory
            if os.path.exists(log_dir):
                try:
                    log_retention_days = config.get("log_retention_days", 30)
                    cleaned_logs = self._clean_directory(log_dir, max_age_days=log_retention_days, pattern="*.log*")
                    cleanup_summary["cleaned_directories"].append({
                        "directory": log_dir,
                        "files_deleted": len(cleaned_logs),
                        "files": cleaned_logs
                    })
                    cleanup_summary["deleted_files"].extend(cleaned_logs)
                except Exception as e:
                    cleanup_summary["errors"].append(f"Failed to clean logs: {e}")
            
            # Clean old backup files
            backup_dir = getattr(settings, "backup_directory", "/backups")
            if os.path.exists(backup_dir):
                try:
                    backup_retention_days = config.get("backup_retention_days", 7)
                    cleaned_backups = self._clean_directory(backup_dir, max_age_days=backup_retention_days)
                    cleanup_summary["cleaned_directories"].append({
                        "directory": backup_dir,
                        "files_deleted": len(cleaned_backups),
                        "files": cleaned_backups
                    })
                    cleanup_summary["deleted_files"].extend(cleaned_backups)
                except Exception as e:
                    cleanup_summary["errors"].append(f"Failed to clean backups: {e}")
            
            # Calculate freed space (approximate)
            total_size = 0
            for file_path in cleanup_summary["deleted_files"]:
                try:
                    total_size += os.path.getsize(file_path) if os.path.exists(file_path) else 0
                except:
                    pass
            
            cleanup_summary["freed_space_mb"] = round(total_size / (1024 * 1024), 2)
            
            return {
                "success": True,
                "cleanup_summary": cleanup_summary
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup files: {e}")
            raise
    
    def _clean_directory(self, directory: str, max_age_days: Optional[int] = None, 
                        max_age_hours: Optional[int] = None, pattern: str = "*") -> List[str]:
        """Clean files in directory based on age."""
        deleted_files = []
        
        try:
            from glob import glob
            import time
            
            search_pattern = os.path.join(directory, pattern)
            files = glob(search_pattern)
            
            cutoff_time = None
            if max_age_days:
                cutoff_time = time.time() - (max_age_days * 24 * 3600)
            elif max_age_hours:
                cutoff_time = time.time() - (max_age_hours * 3600)
            
            if cutoff_time:
                for file_path in files:
                    try:
                        if os.path.isfile(file_path):
                            if os.path.getmtime(file_path) < cutoff_time:
                                os.remove(file_path)
                                deleted_files.append(file_path)
                                logger.debug(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete file {file_path}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to clean directory {directory}: {e}")
        
        return deleted_files


class FileArchiveTask(FileTask):
    """Task to create archives of files and directories."""
    
    def run(self, source_path: str, archive_path: str, archive_type: str = "zip", 
            compression_level: int = 6) -> Dict[str, Any]:
        """Create archive of files."""
        try:
            return self._create_archive(source_path, archive_path, archive_type, compression_level)
        except Exception as e:
            logger.error(f"File archive task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_archive(self, source_path: str, archive_path: str, archive_type: str, 
                       compression_level: int) -> Dict[str, Any]:
        """Create archive from source path."""
        try:
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "error": f"Source path does not exist: {source_path}"
                }
            
            # Ensure archive directory exists
            archive_dir = os.path.dirname(archive_path)
            os.makedirs(archive_dir, exist_ok=True)
            
            archive_info = {
                "source_path": source_path,
                "archive_path": archive_path,
                "archive_type": archive_type,
                "compression_level": compression_level,
                "timestamp": datetime.now().isoformat(),
                "files_archived": 0,
                "archive_size_mb": 0
            }
            
            if archive_type.lower() == "zip":
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                    if os.path.isfile(source_path):
                        zipf.write(source_path, os.path.basename(source_path))
                        archive_info["files_archived"] = 1
                    else:
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, source_path)
                                zipf.write(file_path, arcname)
                                archive_info["files_archived"] += 1
            
            elif archive_type.lower() in ["tar", "tar.gz", "tgz"]:
                mode = "w:gz" if archive_type.lower() in ["tar.gz", "tgz"] else "w"
                with tarfile.open(archive_path, mode) as tarf:
                    if os.path.isfile(source_path):
                        tarf.add(source_path, arcname=os.path.basename(source_path))
                        archive_info["files_archived"] = 1
                    else:
                        tarf.add(source_path, arcname=os.path.basename(source_path))
                        # Count files
                        for root, dirs, files in os.walk(source_path):
                            archive_info["files_archived"] += len(files)
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported archive type: {archive_type}"
                }
            
            # Get archive size
            if os.path.exists(archive_path):
                archive_size = os.path.getsize(archive_path)
                archive_info["archive_size_mb"] = round(archive_size / (1024 * 1024), 2)
            
            logger.info(f"Created archive: {archive_path} ({archive_info['files_archived']} files, {archive_info['archive_size_mb']} MB)")
            
            return {
                "success": True,
                "archive_info": archive_info
            }
            
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            raise


class FileExtractTask(FileTask):
    """Task to extract archives."""
    
    def run(self, archive_path: str, extract_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """Extract archive to specified path."""
        try:
            return self._extract_archive(archive_path, extract_path, overwrite)
        except Exception as e:
            logger.error(f"File extract task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_archive(self, archive_path: str, extract_path: str, overwrite: bool) -> Dict[str, Any]:
        """Extract archive to target directory."""
        try:
            if not os.path.exists(archive_path):
                return {
                    "success": False,
                    "error": f"Archive does not exist: {archive_path}"
                }
            
            if os.path.exists(extract_path) and not overwrite:
                return {
                    "success": False,
                    "error": f"Extract path already exists: {extract_path}"
                }
            
            # Create extract directory
            os.makedirs(extract_path, exist_ok=True)
            
            extract_info = {
                "archive_path": archive_path,
                "extract_path": extract_path,
                "timestamp": datetime.now().isoformat(),
                "files_extracted": 0,
                "extracted_files": []
            }
            
            # Determine archive type by extension
            archive_name = os.path.basename(archive_path).lower()
            
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                    extract_info["files_extracted"] = len(zipf.namelist())
                    extract_info["extracted_files"] = zipf.namelist()
            
            elif any(archive_name.endswith(ext) for ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']):
                mode = "r:*"  # Auto-detect compression
                with tarfile.open(archive_path, mode) as tarf:
                    tarf.extractall(extract_path)
                    extract_info["files_extracted"] = len(tarf.getnames())
                    extract_info["extracted_files"] = tarf.getnames()
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported archive format: {archive_name}"
                }
            
            logger.info(f"Extracted archive: {archive_path} to {extract_path} ({extract_info['files_extracted']} files)")
            
            return {
                "success": True,
                "extract_info": extract_info
            }
            
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            raise


class FileSyncTask(FileTask):
    """Task to synchronize files between directories."""
    
    def run(self, source_dir: str, target_dir: str, sync_mode: str = "mirror", 
            exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronize files between directories."""
        try:
            return self._sync_directories(source_dir, target_dir, sync_mode, exclude_patterns or [])
        except Exception as e:
            logger.error(f"File sync task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _sync_directories(self, source_dir: str, target_dir: str, sync_mode: str, 
                         exclude_patterns: List[str]) -> Dict[str, Any]:
        """Synchronize directories."""
        try:
            if not os.path.exists(source_dir):
                return {
                    "success": False,
                    "error": f"Source directory does not exist: {source_dir}"
                }
            
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            sync_info = {
                "source_dir": source_dir,
                "target_dir": target_dir,
                "sync_mode": sync_mode,
                "timestamp": datetime.now().isoformat(),
                "files_copied": 0,
                "files_updated": 0,
                "files_deleted": 0,
                "errors": []
            }
            
            # TODO: Implement proper directory synchronization
            # For now, implement basic copy operation
            
            try:
                if sync_mode == "mirror":
                    # Remove existing target directory and recreate
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    shutil.copytree(source_dir, target_dir, ignore=shutil.ignore_patterns(*exclude_patterns))
                    
                    # Count files
                    for root, dirs, files in os.walk(target_dir):
                        sync_info["files_copied"] += len(files)
                
                elif sync_mode == "update":
                    # Copy only newer files
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            source_file = os.path.join(root, file)
                            rel_path = os.path.relpath(source_file, source_dir)
                            target_file = os.path.join(target_dir, rel_path)
                            
                            # Check exclude patterns
                            if any(rel_path.match(pattern) for pattern in exclude_patterns):
                                continue
                            
                            # Create target directory if needed
                            target_file_dir = os.path.dirname(target_file)
                            os.makedirs(target_file_dir, exist_ok=True)
                            
                            # Copy if target doesn't exist or source is newer
                            should_copy = False
                            if not os.path.exists(target_file):
                                should_copy = True
                                sync_info["files_copied"] += 1
                            elif os.path.getmtime(source_file) > os.path.getmtime(target_file):
                                should_copy = True
                                sync_info["files_updated"] += 1
                            
                            if should_copy:
                                try:
                                    shutil.copy2(source_file, target_file)
                                except Exception as e:
                                    sync_info["errors"].append(f"Failed to copy {source_file}: {e}")
                
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported sync mode: {sync_mode}"
                    }
                
            except Exception as e:
                sync_info["errors"].append(f"Sync operation failed: {e}")
            
            logger.info(f"Directory sync completed: {source_dir} -> {target_dir}")
            
            return {
                "success": len(sync_info["errors"]) == 0,
                "sync_info": sync_info
            }
            
        except Exception as e:
            logger.error(f"Failed to sync directories: {e}")
            raise


class FileValidationTask(FileTask):
    """Task to validate file integrity and structure."""
    
    def run(self, file_path: str, validation_type: str = "checksum") -> Dict[str, Any]:
        """Validate file integrity."""
        try:
            return self._validate_file(file_path, validation_type)
        except Exception as e:
            logger.error(f"File validation task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_file(self, file_path: str, validation_type: str) -> Dict[str, Any]:
        """Validate file based on specified type."""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File does not exist: {file_path}"
                }
            
            validation_info = {
                "file_path": file_path,
                "validation_type": validation_type,
                "timestamp": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
                "file_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "validation_results": {}
            }
            
            if validation_type == "checksum":
                import hashlib
                
                # Calculate MD5 and SHA256 checksums
                md5_hash = hashlib.md5()
                sha256_hash = hashlib.sha256()
                
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                        sha256_hash.update(chunk)
                
                validation_info["validation_results"] = {
                    "md5": md5_hash.hexdigest(),
                    "sha256": sha256_hash.hexdigest()
                }
            
            elif validation_type == "json":
                # Validate JSON structure
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    validation_info["validation_results"] = {
                        "valid_json": True,
                        "json_keys": list(json_data.keys()) if isinstance(json_data, dict) else None,
                        "json_type": type(json_data).__name__
                    }
                except json.JSONDecodeError as e:
                    validation_info["validation_results"] = {
                        "valid_json": False,
                        "error": str(e)
                    }
            
            elif validation_type == "archive":
                # Validate archive integrity
                archive_name = os.path.basename(file_path).lower()
                
                try:
                    if archive_name.endswith('.zip'):
                        with zipfile.ZipFile(file_path, 'r') as zipf:
                            bad_files = zipf.testzip()
                            validation_info["validation_results"] = {
                                "archive_valid": bad_files is None,
                                "corrupted_files": [bad_files] if bad_files else [],
                                "total_files": len(zipf.namelist())
                            }
                    
                    elif any(archive_name.endswith(ext) for ext in ['.tar', '.tar.gz', '.tgz']):
                        with tarfile.open(file_path, 'r:*') as tarf:
                            # Basic validation - if we can open it, it's likely valid
                            validation_info["validation_results"] = {
                                "archive_valid": True,
                                "total_files": len(tarf.getnames())
                            }
                    
                    else:
                        validation_info["validation_results"] = {
                            "archive_valid": False,
                            "error": "Unsupported archive format"
                        }
                
                except Exception as e:
                    validation_info["validation_results"] = {
                        "archive_valid": False,
                        "error": str(e)
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported validation type: {validation_type}"
                }
            
            return {
                "success": True,
                "validation_info": validation_info
            }
            
        except Exception as e:
            logger.error(f"Failed to validate file: {e}")
            raise


# Task registration
file_cleanup_task = FileCleanupTask()
file_archive_task = FileArchiveTask()
file_extract_task = FileExtractTask()
file_sync_task = FileSyncTask()
file_validation_task = FileValidationTask()