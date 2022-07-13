import json

from sftp_config import SftpConfig
from utils import rprint


class Config:
    BACKUPS_PATH: str = '/backups'
    TEMP_DIR_PATH: str = '/tmp/xtrabackup'
    XTRABACKUP_CONFIG_PATH: str = '/run/secrets/xtrabackup_config.json'
    ERROR_LOG_DIR_PATH: str = '/var/log/xtrabackup'

    user: str = None
    password: str = None
    parallel: int = 10
    sftp: SftpConfig = None

    @staticmethod
    def from_secrets():
        self = Config()

        try:
            with open(Config.XTRABACKUP_CONFIG_PATH, 'r') as config_file:
                try:
                    config = json.load(config_file)
                except json.decoder.JSONDecodeError:
                    raise RuntimeError('Failed to parse the xtrabackup config. Is it valid JSON?')
        except FileNotFoundError:
            raise RuntimeError(f"Config file is missing: [default]/run/secrets/xtrabackup_config.json")

        # check for required options
        required_options = ('user', 'password')
        missing_required_options = tuple(
            filter(lambda required_option: required_option not in config, required_options)
        )
        if len(missing_required_options) > 0:
            raise RuntimeError(f"Config is missing required options: [default]{', '.join(missing_required_options)}")

        # set sftp option
        if 'sftp' in config:
            sftp_config = config.pop('sftp')

            required_sftp_options = ('host', 'user', 'password')
            missing_required_sftp_options = tuple(
                filter(lambda required_option: required_option not in sftp_config, required_sftp_options)
            )
            if len(missing_required_sftp_options) > 0:
                raise RuntimeError(
                    f"SFTP config is missing required options: [default]{', '.join(missing_required_sftp_options)}"
                )

            self.sftp = SftpConfig(**sftp_config)

        # set config options
        for option, value in config.items():
            if hasattr(self, option):
                setattr(self, option, value)
            else:
                message = (
                    f"[yellow3]\\[Config][/yellow3]",
                    'Invalid xtrabackup config option:',
                    f"[red]{option}[/red].",
                    'Skipped.'
                )
                rprint(' '.join(message))

        rprint(f"[blue]\\[Config][/blue] XtraBackup config is ready.")

        return self
