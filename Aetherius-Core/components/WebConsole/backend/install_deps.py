#!/usr/bin/env python3
"""
Install required dependencies for WebConsole backend.
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    """Install all required packages."""
    packages = [
        "alembic>=1.13.0",
        "sqlalchemy[asyncio]>=2.0.23",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "asyncpg>=0.29.0",
        "aiosqlite>=0.19.0",
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "python-dotenv>=1.0.0"
    ]
    
    print("Installing WebConsole backend dependencies...")
    print("=" * 50)
    
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("=" * 50)
    
    if failed_packages:
        print(f"✗ Failed to install {len(failed_packages)} packages:")
        for package in failed_packages:
            print(f"  - {package}")
        sys.exit(1)
    else:
        print(f"✓ Successfully installed all {len(packages)} packages!")
        print("\nYou can now run the migration script:")
        print("python migrations/run_migrations.py init")

if __name__ == "__main__":
    main()