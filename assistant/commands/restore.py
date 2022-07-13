from assistant import Environment
from assistant.configs import Config


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def __call__(self):
        pass

    def execute(self):
        pass
