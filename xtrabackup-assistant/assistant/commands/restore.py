import re
from datetime import datetime
from pathlib import Path, PurePath

from rich.progress import Progress, TextColumn, SpinnerColumn
from rich.prompt import IntPrompt
from rich.text import Text

from configs import Config
from common import Environment, BackupList, Backup
from utils import rprint, now, Sftp


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self.backup_list = BackupList(self._env.xtrabackup_version)

    def execute(self) -> None:
        # get available backups
        self._set_backup_list()

        if len(self.backup_list) == 0:
            rprint(Text.assemble(
                ('[Assistant] ', 'blue'),
                ('Not found available backups.', 'orange1')
            ))
            return None

        # ask choice a backup
        self.backup_list.print()
        target_backup_no = IntPrompt.ask(
            prompt=Text.assemble(('Please enter no of the target backup', 'blue')),
            choices=self.backup_list.available_numbers,
            show_choices=False
        )
        target_backup: Backup = self.backup_list[target_backup_no - 1]

        rprint(f"[green3]Target backup:[/green3] {target_backup.filename}")

        if target_backup.source == 'sftp':
            self._download_backup(target_backup)

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
        with Sftp(self._config.sftp) as sftp:
            current_year_backups_path = PurePath(self._config.sftp.path, now('%Y'))
            return list(map(
                lambda backup: Backup(source='sftp', path=backup['path'], size=backup['attr'].st_size),
                sftp.r_find_files(current_year_backups_path, re.compile('.tar$'))
            ))

    def _download_backup(self, backup: Backup) -> None:
        with Sftp(self._config.sftp) as sftp:
            backup_year = datetime.strptime(backup.date, '%Y-%m-%d %H:%M').strftime('%Y')
            backup_month = datetime.strptime(backup.date, '%Y-%m-%d %H:%M').strftime('%m')
            sftp.download(backup.path, Path(Config.BACKUPS_PATH, backup_year, backup_month, backup.path.name))
