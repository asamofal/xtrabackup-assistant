from common import Environment
from configs import Config
from utils import Slack
from .commands import Command, CreateCommand, RestoreCommand


class Assistant:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self, command: Command) -> None:
        if command in [Command.CREATE, Command.CREATE_UPLOAD]:
            try:
                upload = command is Command.CREATE_UPLOAD
                CreateCommand(self._env, self._config).execute(upload)
            except RuntimeError as e:
                if self._config.slack is not None:
                    Slack(self._config.slack).notify(project=self._config.project_name, error=e)
                raise
        elif command is Command.RESTORE:
            RestoreCommand(self._env, self._config).execute()
