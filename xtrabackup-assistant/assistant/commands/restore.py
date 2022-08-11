import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path, PurePath

from rich.progress import Progress, TextColumn, SpinnerColumn, BarColumn, TaskProgressColumn, DownloadColumn
from rich.prompt import IntPrompt
from rich.text import Text

from common import Environment, BackupList, Backup
from configs import Config
from constants import BACKUPS_DIR_PATH, TEMP_DIR_PATH
from utils import rprint, now, Sftp, echo


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self.backup_list = BackupList(self._env.xtrabackup_version)
        self.target_backup = None

    def execute(self) -> None:
        # get available backups
        self._set_backup_list()

        if len(self.backup_list) == 0:
            echo(text='Not found available backups.', style='orange1', time=False)
            return None

        # ask choice a backup
        self.backup_list.print()
        target_backup_no = IntPrompt.ask(
            prompt=Text('Please enter no of the target backup', 'blue'),
            choices=self.backup_list.available_numbers,
            show_choices=False
        )
        self.target_backup = self.backup_list[target_backup_no - 1]

        echo(
            Text.assemble(('Target backup: ', 'green3'), (self.target_backup.filename, 'default')),
            time=False
        )

        if self.target_backup.source == 'sftp':
            self._download_backup(self.target_backup)

        self._extract_backup_from_archive()
        # self._extract_xbstream()
        # self._decompress_backup()
        # self._prepare_backup()

    def _set_backup_list(self):
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            transient=True
        ) as progress:
            progress.add_task('[blue]Searching for available backups...')

            self.backup_list.extend(self._local_this_year_backups())

            # if self._config.sftp is not None:
            #     self.backup_list.extend(self._sftp_this_year_backups())

    @staticmethod
    def _local_this_year_backups() -> list:
        current_year_backups_path = Path(BACKUPS_DIR_PATH, now('%Y'))
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
            sftp.download(backup.path, Path(BACKUPS_DIR_PATH, backup_year, backup_month, backup.path.name))

    def _extract_backup_from_archive(self) -> None:
        with Progress(
            TextColumn('[blue]\\[tar][/blue]'),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            transient=True
        ) as progress:
            echo('Start extracting backup file from the archive.', 'tar')

            with tarfile.open(self.target_backup.path, 'r:') as tar:
                backup_file = next(
                    (backup for backup in tar.getmembers() if re.search('.xbstream$', backup.name)),
                    None
                )
                if backup_file is None:
                    raise RuntimeError('Not found .xbstream backup file in the target archive')

                # extract with progress bar
                # noinspection PyTypeChecker
                with progress.wrap_file(
                    file=tar.extractfile(backup_file),
                    total=backup_file.size,
                    description='[blue]Extracting a backup file...'
                ) as source:
                    with open(Path(TEMP_DIR_PATH, backup_file.name), 'wb') as destination:
                        shutil.copyfileobj(source, destination)
            progress.stop()

            echo('Backup file extracted.', 'tar')

    def _decompress_backup(self):
        pass

    def _extract_xbstream(self) -> None:
        echo()
        rprint(Text.assemble(
            ('[tar] ', 'blue'),
            (f"[{now('%Y-%m-%d %H:%M:%S')}] ", 'default'),
            ('Backup file extracted.', 'default')
        ))
