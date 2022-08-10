import os
import shutil

from common import Environment
from configs import Config
from constants import TEMP_DIR_PATH
from .commands import Command, CreateCommand, RestoreCommand


class Assistant:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self, command: Command) -> None:
        if command is Command.CREATE:
            CreateCommand(self._env, self._config).execute()
        elif command is Command.RESTORE:
            RestoreCommand(self._env, self._config).execute()

    @staticmethod
    def clear_temp_dir() -> None:
        with os.scandir(str(Config.TEMP_DIR_PATH)) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)

        version_check_log = '/tmp/percona-version-check'
        if os.path.exists(version_check_log):
            os.remove(version_check_log)
