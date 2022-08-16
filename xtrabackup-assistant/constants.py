from pathlib import Path

ROOT_DIR: Path = Path(__file__).parent.parent.absolute()

BACKUPS_DIR_PATH: Path = Path(ROOT_DIR, 'data/backups')
TEMP_DIR_PATH: Path = Path(ROOT_DIR, 'data/tmp')
ERROR_LOG_DIR_PATH: Path = Path(ROOT_DIR, 'logs')
RESTORE_DIR_PATH: Path = Path(ROOT_DIR, 'data/restore')
CONFIG_PATH: Path = Path('/run/secrets/xa_config.json')
ALT_CONFIG_PATH: Path = Path(ROOT_DIR, 'config.json')
