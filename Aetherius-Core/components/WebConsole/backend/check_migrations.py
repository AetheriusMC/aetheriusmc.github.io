#!/usr/bin/env python3
"""Check migration status."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from app.core.config import settings

def check_migrations():
    migrations_dir = Path(__file__).parent / 'migrations'
    alembic_ini_path = migrations_dir / 'alembic.ini'
    
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option('script_location', str(migrations_dir))
    alembic_cfg.set_main_option('sqlalchemy.url', settings.database.url)
    
    print('Current revision:')
    command.current(alembic_cfg)
    
    print('\nMigration history:')
    command.history(alembic_cfg)
    
    print('\nRunning upgrade to head...')
    command.upgrade(alembic_cfg, 'head')
    
    print('\nFinal status:')
    command.current(alembic_cfg)

if __name__ == "__main__":
    check_migrations()