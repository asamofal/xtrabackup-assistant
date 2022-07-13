import os
import shutil

from assistant import Environment
from assistant.commands import Command
from assistant.commands.create import CreateCommand
from assistant.commands.restore import RestoreCommand
from assistant.configs import Config


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
        with os.scandir(Config.TEMP_DIR_PATH) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)

        version_check_log = f"/tmp/percona-version-check"
        if os.path.exists(version_check_log):
            os.remove(version_check_log)
