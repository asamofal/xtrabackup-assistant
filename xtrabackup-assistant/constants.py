from pathlib import Path

ROOT_DIR: Path = Path(__file__).parent.parent.absolute()

CONFIG_PATH: Path = Path(ROOT_DIR, 'conf/config.json')

BACKUPS_DIR_PATH: Path = Path(ROOT_DIR, 'data/backups')
TEMP_DIR_PATH: Path = Path(ROOT_DIR, 'data/tmp')
RESTORE_DIR_PATH: Path = Path(ROOT_DIR, 'data/restore')

LOGS_DIR_PATH: Path = Path(ROOT_DIR, 'logs')
PRIMARY_LOG_PATH: Path = Path(LOGS_DIR_PATH, 'xtrabackup-assistant.log')
