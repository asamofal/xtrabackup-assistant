import json

from rich.text import Text

from configs import XtrabackupConfig, SftpConfig, SlackConfig
from constants import CONFIG_PATH, ALT_CONFIG_PATH
from exceptions import ConfigError
from utils import echo_warning, echo


class Config:
    CONFIG_STRUCTURE: dict = {
        'project_name': {
            'optional': False,
            'required_fields': {}
        },
        'xtrabackup': {
            'optional': False,
            'required_fields': {'user', 'password'}
        },
        'sftp': {
            'optional': True,
            'required_fields': {'host', 'user', 'password'}
        },
        'slack': {
            'optional': True,
            'required_fields': {'token', 'channel'}
        }
    }

    project_name: str = None
    xtrabackup: XtrabackupConfig = None
    sftp: SftpConfig = None
    slack: SlackConfig = None

    _raw_config: dict = None

    def __init__(self):
        config_path = CONFIG_PATH if CONFIG_PATH.exists() else ALT_CONFIG_PATH

        try:
            with open(config_path, 'r') as config_file:
                try:
                    self._raw_config = json.load(config_file)
                except json.decoder.JSONDecodeError:
                    raise ConfigError('Failed to parse the config. Is it valid JSON?')
        except FileNotFoundError:
            raise ConfigError(f"Config file is missing: [default]{CONFIG_PATH} or {ALT_CONFIG_PATH}")

        self.validate_config()

        self.project_name = self._raw_config['project_name']
        self.xtrabackup = XtrabackupConfig(**self._raw_config['xtrabackup'])
        if 'sftp' in self._raw_config:
            self.sftp = SftpConfig(**self._raw_config['sftp'])
        if 'slack' in self._raw_config:
            self.slack = SlackConfig(**self._raw_config['slack'])

    def validate_config(self):
        # check for unknown top lvl nodes
        unknown_nodes = [node for node in self._raw_config.keys() if node not in self.CONFIG_STRUCTURE.keys()]
        if len(unknown_nodes) > 0:
            echo_warning(Text.assemble(
                ('Unknown config nodes: ', 'dark_orange'),
                (f"{', '.join(unknown_nodes)}", 'red bold'),
                ('. Skipped.', 'dark_orange')
            ), author='Config')
            # remove unknown nodes from the config
            self._raw_config = dict((k, v) for k, v in self._raw_config.items() if k not in unknown_nodes)

        # check for required top lvl nodes
        required_nodes = [key for key, value in self.CONFIG_STRUCTURE.items() if value['optional'] is False]
        missing_required_nodes = [node for node in required_nodes if node not in self._raw_config.keys()]
        if len(missing_required_nodes) > 0:
            raise ConfigError(f"Missing required config nodes: [default]{', '.join(missing_required_nodes)}")

        # check for existing node fields
        for node_name, node_fields in self._raw_config.items():
            required_node_fields = self.CONFIG_STRUCTURE[node_name]['required_fields']
            node_missing_required_fields = [
                f"{node_name}.{field}" for field in required_node_fields if field not in node_fields
            ]
            if len(node_missing_required_fields) > 0:
                message = f"Missing required config fields: [default]{', '.join(node_missing_required_fields)}"
                raise ConfigError(message)

    @staticmethod
    def print_ready_message():
        echo(text='Config is ready.', style='green3', author='Config', time=False)
