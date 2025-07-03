"""
Backup related tasks.
"""

import os
import shutil
import tarfile
import gzip
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from celery import shared_task

from .base import ProgressTask, log_task_execution, task_with_retry

import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=ProgressTask)
@log_task_execution
@task_with_retry(max_retries=2, default_retry_delay=300)
def create_backup(
    self,
    backup_name: Optional[str] = None,
    backup_type: str = "full",
    include_worlds: bool = True,
    include_plugins: bool = True,
    include_config: bool = True,
    compression: bool = True
) -> Dict[str, Any]:
    """Create a server backup."""
    
    if not backup_name:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / f"{backup_name}.tar.gz" if compression else backup_dir / backup_name
    
    try:
        # Determine what to backup
        backup_paths = []
        
        if include_worlds:
            # TODO: Get world paths from Aetherius Core
            world_paths = ["world", "world_nether", "world_the_end"]
            for world_path in world_paths:
                if Path(world_path).exists():
                    backup_paths.append(("worlds", world_path))
        
        if include_plugins:
            # TODO: Get plugin paths from Aetherius Core
            plugin_paths = ["plugins"]
            for plugin_path in plugin_paths:
                if Path(plugin_path).exists():
                    backup_paths.append(("plugins", plugin_path))
        
        if include_config:
            # TODO: Get config paths from Aetherius Core
            config_paths = ["server.properties", "bukkit.yml", "spigot.yml", "paper.yml"]
            for config_path in config_paths:
                if Path(config_path).exists():
                    backup_paths.append(("config", config_path))
        
        total_files = sum(
            len(list(Path(path).rglob("*"))) if Path(path).is_dir() else 1
            for _, path in backup_paths
        )
        
        self.update_progress(0, total_files, "Starting backup...")
        
        if compression:
            # Create compressed backup
            with tarfile.open(backup_path, "w:gz") as tar:
                processed_files = 0
                
                for category, path in backup_paths:
                    path_obj = Path(path)
                    
                    if path_obj.is_file():
                        tar.add(path, arcname=f"{category}/{path_obj.name}")
                        processed_files += 1
                        self.update_progress(
                            processed_files, 
                            total_files, 
                            f"Backing up {category}: {path_obj.name}"
                        )
                    
                    elif path_obj.is_dir():
                        for file_path in path_obj.rglob("*"):
                            if file_path.is_file():
                                arcname = f"{category}/{file_path.relative_to(path_obj.parent)}"
                                tar.add(file_path, arcname=arcname)
                                processed_files += 1
                                
                                if processed_files % 10 == 0:  # Update progress every 10 files
                                    self.update_progress(
                                        processed_files,
                                        total_files,
                                        f"Backing up {category}: {file_path.name}"
                                    )
        else:
            # Create uncompressed backup
            backup_path.mkdir(parents=True, exist_ok=True)
            processed_files = 0
            
            for category, path in backup_paths:
                category_dir = backup_path / category
                category_dir.mkdir(exist_ok=True)
                
                path_obj = Path(path)
                
                if path_obj.is_file():
                    shutil.copy2(path_obj, category_dir / path_obj.name)
                    processed_files += 1
                    self.update_progress(
                        processed_files,
                        total_files,
                        f"Backing up {category}: {path_obj.name}"
                    )
                
                elif path_obj.is_dir():
                    dest_dir = category_dir / path_obj.name
                    shutil.copytree(path_obj, dest_dir, dirs_exist_ok=True)
                    
                    # Count copied files for progress
                    for file_path in dest_dir.rglob("*"):
                        if file_path.is_file():
                            processed_files += 1
                            
                            if processed_files % 10 == 0:
                                self.update_progress(
                                    processed_files,
                                    total_files,
                                    f"Backing up {category}: {file_path.name}"
                                )
        
        # Get backup size
        if compression:
            backup_size = backup_path.stat().st_size
        else:
            backup_size = sum(
                f.stat().st_size for f in backup_path.rglob("*") if f.is_file()
            )
        
        self.update_progress(total_files, total_files, "Backup completed successfully")
        
        return {
            "success": True,
            "backup_name": backup_name,
            "backup_path": str(backup_path),
            "backup_size": backup_size,
            "backup_type": backup_type,
            "compression": compression,
            "files_backed_up": total_files,
            "created_at": datetime.now().isoformat(),
            "includes": {
                "worlds": include_worlds,
                "plugins": include_plugins,
                "config": include_config
            }
        }
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        
        # Cleanup partial backup
        if backup_path.exists():
            if backup_path.is_file():
                backup_path.unlink()
            else:
                shutil.rmtree(backup_path)
        
        raise


@shared_task(bind=True, base=ProgressTask)
@log_task_execution
@task_with_retry(max_retries=1, default_retry_delay=300)
def restore_backup(
    self,
    backup_path: str,
    restore_worlds: bool = True,
    restore_plugins: bool = True,
    restore_config: bool = True,
    create_backup_before_restore: bool = True
) -> Dict[str, Any]:
    """Restore from a backup."""
    
    backup_file = Path(backup_path)
    
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    try:
        # Create backup before restore if requested
        if create_backup_before_restore:
            self.update_progress(0, 100, "Creating backup before restore...")
            pre_restore_backup = create_backup.delay(
                backup_name=f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                backup_type="pre_restore"
            )
            pre_restore_backup.wait()  # Wait for backup to complete
        
        self.update_progress(10, 100, "Extracting backup...")
        
        # Extract backup
        if backup_file.suffix == ".gz" or backup_file.suffixes == [".tar", ".gz"]:
            # Compressed backup
            with tarfile.open(backup_file, "r:gz") as tar:
                members = tar.getmembers()
                total_members = len(members)
                
                for i, member in enumerate(members):
                    # Determine restore path based on category
                    path_parts = Path(member.name).parts
                    if len(path_parts) < 2:
                        continue
                    
                    category = path_parts[0]
                    relative_path = Path(*path_parts[1:])
                    
                    should_restore = (
                        (category == "worlds" and restore_worlds) or
                        (category == "plugins" and restore_plugins) or
                        (category == "config" and restore_config)
                    )
                    
                    if should_restore:
                        # TODO: Map to actual server paths
                        restore_path = Path(relative_path)
                        
                        # Extract file
                        member.name = str(relative_path)  # Remove category prefix
                        tar.extract(member, path=".")
                    
                    # Update progress
                    progress = 10 + int((i / total_members) * 80)
                    self.update_progress(
                        progress, 
                        100, 
                        f"Restoring: {member.name}"
                    )
        
        else:
            # Uncompressed backup
            backup_dir = backup_file
            
            categories = []
            if restore_worlds and (backup_dir / "worlds").exists():
                categories.append("worlds")
            if restore_plugins and (backup_dir / "plugins").exists():
                categories.append("plugins")
            if restore_config and (backup_dir / "config").exists():
                categories.append("config")
            
            total_files = sum(
                len(list((backup_dir / category).rglob("*")))
                for category in categories
            )
            
            processed_files = 0
            
            for category in categories:
                category_dir = backup_dir / category
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        # TODO: Map to actual server paths
                        relative_path = file_path.relative_to(category_dir)
                        dest_path = Path(relative_path)
                        
                        # Create parent directories
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(file_path, dest_path)
                        
                        processed_files += 1
                        progress = 10 + int((processed_files / total_files) * 80)
                        self.update_progress(
                            progress,
                            100,
                            f"Restoring {category}: {file_path.name}"
                        )
        
        self.update_progress(100, 100, "Restore completed successfully")
        
        return {
            "success": True,
            "backup_path": backup_path,
            "restored_at": datetime.now().isoformat(),
            "restored": {
                "worlds": restore_worlds,
                "plugins": restore_plugins,
                "config": restore_config
            },
            "pre_restore_backup_created": create_backup_before_restore
        }
        
    except Exception as e:
        logger.error(f"Backup restoration failed: {e}")
        raise


@shared_task
@log_task_execution
def cleanup_old_backups(retention_days: int = 30) -> Dict[str, Any]:
    """Clean up old backup files."""
    
    backup_dir = Path("data/backups")
    if not backup_dir.exists():
        return {"success": True, "deleted_count": 0, "message": "No backup directory found"}
    
    cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
    deleted_count = 0
    deleted_files = []
    
    try:
        for backup_file in backup_dir.iterdir():
            if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_time:
                file_size = backup_file.stat().st_size
                backup_file.unlink()
                deleted_count += 1
                deleted_files.append({
                    "name": backup_file.name,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                })
        
        logger.info(f"Cleaned up {deleted_count} old backup files")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_files": deleted_files,
            "retention_days": retention_days
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": deleted_count
        }


@shared_task
@log_task_execution
def check_backup_schedule() -> Dict[str, Any]:
    """Check if scheduled backups need to be created."""
    
    # TODO: Implement backup scheduling logic
    # This would check configuration for backup schedules and create backups as needed
    
    logger.info("Checking backup schedule...")
    
    return {
        "success": True,
        "message": "Backup schedule check completed",
        "backups_created": 0
    }