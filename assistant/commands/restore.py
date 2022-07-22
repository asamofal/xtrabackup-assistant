import re
from collections import UserList
from datetime import datetime
from pathlib import Path, PurePath

from humanize import naturalsize
from packaging import version
from rich.progress import Progress, TextColumn, SpinnerColumn
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.text import Text

from assistant import Environment, SftpClient
from assistant.configs import Config
from utils import rprint, now


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self.backup_list = BackupsList(self._env.xtrabackup_version)

    def execute(self) -> None:
        self._set_backup_list()
        if len(self.backup_list) == 0:
            rprint(Text.assemble(
                ('[Assistant] ', 'blue'),
                ('Not found available backups.', 'orange1')
            ))
            return None

        self.backup_list.print()
        target_backup_no = IntPrompt.ask(
            prompt=Text.assemble(('Please enter no of the target backup', 'blue')),
            choices=self.backup_list.numbers,
            show_choices=False
        )
        target_backup = self.backup_list[target_backup_no - 1]
        rprint(target_backup.path)
        # if target_backup.source == 'sftp':
        #     with SftpClient(self._config.sftp) as sftp:
        #         sftp.download(target_backup.path, Path(Config.BACKUPS_PATH, '2022/07', target_backup.path.name))

    def _set_backup_list(self):
        with Progress(
                SpinnerColumn(),
                TextColumn('[progress.description]{task.description}'),
                transient=True
        ) as progress:
            progress.add_task('[blue]Searching for available backups...')

            self.backup_list.extend(self._local_this_year_backups())

            if self._config.sftp is not None:
                self.backup_list.extend(self._sftp_this_year_backups())

    def _local_this_year_backups(self) -> list:
        current_year_backups_path = Path(self._config.BACKUPS_PATH, now('%Y'))
        return list(map(
            lambda path: Backup(source='local', path=path, size=path.stat().st_size),
            current_year_backups_path.rglob('*.tar')
        ))

    def _sftp_this_year_backups(self) -> list:
        with SftpClient(self._config.sftp) as sftp:
            current_year_backups_path = PurePath(self._config.sftp.path, now('%Y'))
            return list(map(
                lambda backup: Backup(source='sftp', path=backup['path'], size=backup['attr'].st_size),
                sftp.r_find_files(current_year_backups_path, re.compile('.tar$'))
            ))


class Backup:
    def __init__(self, source: str, path: PurePath, size: int):
        self.source = source
        self.path = path
        self.size = naturalsize(size)

    @property
    def date(self) -> str:
        return datetime.strptime(self.filename.split('_')[0], '%Y-%m-%d-%H-%M').strftime('%Y-%m-%d %H:%M')

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def mysql_version(self) -> str:
        return self.path.stem.split('_')[-1]


class BackupsList(UserList):
    def __init__(self, xtrabackup_version: str):
        super().__init__()

        self._xtrabackup_version = xtrabackup_version

    def append(self, backup: Backup) -> None:
        if backup not in self and self._is_compatible(backup):
            super().append(backup)

        super().sort(key=lambda b: b.date, reverse=True)

    def extend(self, backups: list) -> None:
        for backup in backups:
            self.append(backup)

    def _is_compatible(self, backup: Backup) -> bool:
        return version.parse(backup.mysql_version) <= version.parse(self._xtrabackup_version)

    def print(self) -> None:
        title = f"Available backups (supported by Percona XtraBackup {self._xtrabackup_version})"
        table = Table(title=title)

        table.add_column('No')
        table.add_column('Source')
        table.add_column('Date', no_wrap=True)
        table.add_column('Filename', no_wrap=True)
        table.add_column('Size')

        for index, backup in enumerate(self):
            table.add_row(str(index + 1), backup.source, backup.date, backup.filename, backup.size)

        return rprint(table)

    @property
    def numbers(self) -> list:
        return [str(i) for i in range(1, len(self) + 1)]

    def __contains__(self, item: Backup) -> bool:
        duplicate = next((backup for backup in self.data if backup.filename == item.filename), None)

        return duplicate is not None
