from rich.text import Text

from assistant import Environment
from assistant.configs import Config
from utils import is_mysql_running, rprint


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self):
        if is_mysql_running():
            message = Text.assemble(
                ('Please restart the container with env variable: ', 'yellow3'),
                ('XTRABACKUP_RESTORE=true', 'blue bold')
            )
            rprint(message)

            raise RuntimeError('MySQL server needs to be shut down before restore is performed.')

        rprint('Restoring...')
