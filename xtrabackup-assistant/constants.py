from pathlib import Path

ROOT_DIR: Path = Path().parent.resolve()

BACKUPS_DIR_PATH: Path = Path(ROOT_DIR, 'data/backups')
TEMP_DIR_PATH: Path = Path(ROOT_DIR, 'data/tmp')
ERROR_LOG_DIR_PATH: Path = Path(ROOT_DIR, 'logs')
CONFIG_PATH: Path = Path('/run/secrets/xtrabackup_config.json')
ALT_CONFIG_PATH: Path = Path(ROOT_DIR, 'config.json')
