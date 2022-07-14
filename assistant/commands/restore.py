from assistant import Environment
from assistant.configs import Config
from utils import is_mysql_running


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def execute(self):
        print(is_mysql_running())
