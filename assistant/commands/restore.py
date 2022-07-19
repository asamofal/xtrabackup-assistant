import re

from packaging import version

from assistant import Environment
from assistant.configs import Config
from utils import rprint


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self):
        local_suitable_backups = self._local_suitable_backups()
        print(local_suitable_backups)

    def _local_suitable_backups(self) -> list:
        all_local_backups = list(Config.BACKUPS_PATH.rglob('*.tar'))

        suitable_local_backups = []
        for backup_path in all_local_backups:
            backup_mysql_version = version.parse(re.split('_', backup_path.stem)[-1])
            min_target_mysql_version = version.parse(self._env.xtrabackup_version)
            if backup_mysql_version <= min_target_mysql_version:
                suitable_local_backups.append(backup_path)

        return suitable_local_backups
