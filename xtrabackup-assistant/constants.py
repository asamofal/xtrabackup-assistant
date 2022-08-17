from pathlib import Path

ROOT_DIR: Path = Path(__file__).parent.parent.absolute()

BACKUPS_DIR_PATH: Path = Path(ROOT_DIR, 'data/backups')
TEMP_DIR_PATH: Path = Path(ROOT_DIR, 'data/tmp')
ERROR_LOG_DIR_PATH: Path = Path(ROOT_DIR, 'logs')
RESTORE_DIR_PATH: Path = Path(ROOT_DIR, 'data/restore')
LOGS_DIR_PATH: Path = Path(ROOT_DIR, 'logs')
PRIMARY_LOG_PATH: Path = Path(LOGS_DIR_PATH, 'xtrabackup-assistant.log')
CONFIG_PATH: Path = Path('/run/secrets/xa_config.json')
ALT_CONFIG_PATH: Path = Path(ROOT_DIR, 'config.json')
