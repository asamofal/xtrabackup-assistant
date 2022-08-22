from common import Environment
from configs import Config
from utils import Slack
from .commands import Command, CreateCommand, RestoreCommand, RotateCommand


class Assistant:
    def __init__(self, config: Config):
        self._config = config

    def execute(self, command: Command) -> None:
        if command in [Command.CREATE, Command.CREATE_UPLOAD]:
            env = Environment()
            env.print_versions()
            try:
                upload = command is Command.CREATE_UPLOAD
                CreateCommand(env, self._config).execute(upload)
            except RuntimeError as e:
                if self._config.slack is not None:
                    Slack(self._config.slack).notify(project=self._config.project_name, error=e)
                raise
        elif command is Command.RESTORE:
            env = Environment()
            env.print_versions()
            RestoreCommand(env, self._config).execute()
        elif command is Command.ROTATE:
            RotateCommand(self._config).execute()
