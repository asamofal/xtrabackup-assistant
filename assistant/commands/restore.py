import re
from datetime import datetime

from humanize import naturalsize
from packaging import version
from rich.progress import Progress, TextColumn, SpinnerColumn
from rich.table import Table

from assistant import Environment, SftpClient
from assistant.configs import Config
from utils import rprint


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self.available_backups = {'local': [], 'sftp': []}

    def execute(self) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            transient=True
        ) as progress:
            progress.add_task('[blue]Searching for available backups...')

            self.available_backups['local'] = self._local_suitable_backups()

            if self._config.sftp is not None:
                self.available_backups['sftp'] = self._sftp_suitable_backups()

        self.display_available_backups()

    def _local_suitable_backups(self) -> list:
        all_local_backups = list(
            map(lambda path: {'path': path, 'attr': path.stat()}, Config.BACKUPS_PATH.rglob('*.tar'))
        )

        local_suitable_backups = self._filter_only_supported_versions(all_local_backups)

        local_backups = []
        for backup in local_suitable_backups:
            date = datetime.strptime(backup['path'].name.split('_')[0], '%Y-%m-%d-%H-%M').strftime('%Y-%m-%d %H:%M')
            local_backups.append({
                'source': 'local',
                'date': date,
                'filename': backup['path'].name,
                'size': naturalsize(backup['attr'].st_size)
            })

        return local_backups

    def _sftp_suitable_backups(self) -> list:
        with SftpClient(self._config.sftp) as sftp:
            all_sftp_backups = sftp.r_find_files(self._config.sftp.path, re.compile('.tar$'))

        sftp_suitable_backups = self._filter_only_supported_versions(all_sftp_backups)

        sftp_backups = []
        for backup in sftp_suitable_backups:
            date = datetime.strptime(backup['path'].name.split('_')[0], '%Y-%m-%d-%H-%M').strftime('%Y-%m-%d %H:%M')
            sftp_backups.append({
                'source': 'sftp',
                'date': date,
                'filename': backup['path'].name,
                'size': naturalsize(backup['attr'].st_size)
            })

        return sftp_backups

    def _filter_only_supported_versions(self, backups: list) -> list:
        suitable_backups = []
        for backup in backups:
            backup_mysql_version = version.parse(re.split('_', backup['path'].stem)[-1])
            max_supported_mysql_version = version.parse(self._env.xtrabackup_version)
            if backup_mysql_version <= max_supported_mysql_version:
                suitable_backups.append(backup)

        return suitable_backups

    def display_available_backups(self):
        title = f"Available backups (supported by Percona XtraBackup {self._env.xtrabackup_version})"
        table = Table(title=title)

        table.add_column('Source', no_wrap=True)
        table.add_column('Date', no_wrap=True)
        table.add_column('Filename', no_wrap=True)
        table.add_column('Size')

        for backup in self.available_backups['local']:
            table.add_row(backup['source'], backup['date'], backup['filename'], backup['size'])

        for backup in self.available_backups['sftp']:
            table.add_row(backup['source'], backup['date'], backup['filename'], backup['size'])

        rprint(table)
