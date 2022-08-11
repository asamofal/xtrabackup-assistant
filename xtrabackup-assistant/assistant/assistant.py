from common import Environment
from configs import Config
from .commands import Command, CreateCommand, RestoreCommand


class Assistant:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self, command: Command) -> None:
        if command in [Command.CREATE, Command.CREATE_NO_UPLOAD]:
            is_upload = command is Command.CREATE
            CreateCommand(self._env, self._config).execute(is_upload)
        elif command is Command.RESTORE:
            RestoreCommand(self._env, self._config).execute()
