import re
import shutil
import subprocess
import tarfile
import threading
from datetime import datetime
from pathlib import Path, PurePath
from time import sleep
from typing import Union

from rich.progress import Progress, TextColumn, SpinnerColumn, BarColumn, TaskProgressColumn, DownloadColumn, \
    MofNCompleteColumn
from rich.prompt import IntPrompt
from rich.text import Text

from common import Environment, BackupList, Backup
from configs import Config
from constants import BACKUPS_DIR_PATH, TEMP_DIR_PATH, RESTORE_DIR_PATH
from utils import now, Sftp, echo, clear_dir


class RestoreCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self.backup_list = BackupList(self._env.xtrabackup_version)
        self.target_backup: Union[Backup, None] = None

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
            Text.assemble(('Target backup: ', 'green3'), (self.target_backup.filename, 'italic')),
            time=False
        )

        if self.target_backup.source == 'sftp':
            self._download_backup(self.target_backup)

        try:
            self._extract_xbstream_file_from_archive()
            self._extract_qp_files_from_xbstream_file()
            self._decompress_qp_files()
            self._prepare_mysql_files()
        except (RuntimeError, KeyboardInterrupt) as e:
            clear_dir(RESTORE_DIR_PATH)

            if isinstance(e, KeyboardInterrupt):
                raise

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

    def _extract_xbstream_file_from_archive(self) -> None:
        echo('Start extracting xbstream file from the archive', 'tar')

        with tarfile.open(self.target_backup.path, 'r:') as tar:
            backup_file = next(
                (backup for backup in tar.getmembers() if re.search('.xbstream$', backup.name)),
                None
            )
            if backup_file is None:
                raise RuntimeError('Not found .xbstream backup file in the target archive')

            with Progress(
                TextColumn('[blue]\\[tar][/blue]'),
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                DownloadColumn(),
                transient=True
            ) as progress:
                # extract with progress bar
                # noinspection PyTypeChecker
                with progress.wrap_file(
                    file=tar.extractfile(backup_file),
                    total=backup_file.size,
                    description='[blue]Extracting xbstream file...'
                ) as source:
                    with open(Path(TEMP_DIR_PATH, backup_file.name), 'wb') as destination:
                        shutil.copyfileobj(source, destination)

        echo('xbstream file extracted', 'tar')

    def _extract_qp_files_from_xbstream_file(self) -> None:
        echo('Start extracting qpress files from xbstream file', 'xbstream')

        with Progress(
            TextColumn('[blue]\\[xbstream][/blue]'),
            SpinnerColumn(),
            TextColumn('[blue]Extracting qpress files...'),
            transient=True
        ) as progress:
            try:
                target_backup_name = self.target_backup.path.stem
                xbstream_file_path = Path(TEMP_DIR_PATH, f'{target_backup_name}.xbstream')
                with progress.open(xbstream_file_path, 'rb') as xbstream_file:
                    command_options = (
                        f'--parallel={self._config.xtrabackup.parallel}',
                        '-C',
                        RESTORE_DIR_PATH,
                        '-x',
                    )
                    command = subprocess.run(
                        ['xbstream', *command_options],
                        stdin=xbstream_file,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if command.returncode != 0:
                        raise RuntimeError('Failed to extract files from xbstream')
            except FileNotFoundError:
                raise RuntimeError(f'Failed to extract from xbstream: file not found {xbstream_file_path}')

        echo('qpress files extracted', 'xbstream')

    # noinspection PyMethodMayBeStatic
    def _decompress_qp_files(self) -> None:
        echo('Start decompressing qpress files', 'xtrabackup')

        progress_thread = threading.Thread(
            target=print_progress_decompressing_qp_files,
            name='decompression_progress_tread')
        progress_thread.start()

        command_options = (
            '--decompress',
            f'--target-dir={RESTORE_DIR_PATH}',
            f'--parallel={self._config.xtrabackup.parallel}',
            '--decompress-threads=5',
            '--remove-original'
        )
        command = subprocess.run(
            ['xtrabackup', *command_options],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # wait until progress disappear
        progress_thread.join()

        if command.returncode != 0:
            raise RuntimeError('Failed to decompress qpress files')

        echo('qpress files decompressed', 'xtrabackup')

    @staticmethod
    def _prepare_mysql_files() -> None:
        echo('Start preparing mysql files', 'xtrabackup')

        with Progress(
            TextColumn('[blue]\\[xtrabackup][/blue]'),
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            transient=True
        ) as progress:
            progress.add_task('[blue]Preparing mysql files...')

            command_options = (
                '--prepare',
                f'--target-dir={RESTORE_DIR_PATH}'
            )
            command = subprocess.run(
                ['xtrabackup', *command_options],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if command.returncode != 0:
                raise RuntimeError('Failed to prepare backup files')

        echo('mysql files are ready', 'xtrabackup')


def print_progress_decompressing_qp_files():
    with Progress(
        TextColumn('[blue]\\[xtrabackup][/blue]'),
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        MofNCompleteColumn(),
        transient=True
    ) as progress:
        qp_files_total_count = len(list(RESTORE_DIR_PATH.rglob('*.qp')))
        decompressing = progress.add_task('[blue]Decompressing qpress files...', total=qp_files_total_count)

        qp_files_left_count = qp_files_total_count
        while qp_files_left_count > 0:
            qp_files_left_count = len(list(RESTORE_DIR_PATH.rglob('*.qp')))
            completed = qp_files_total_count - qp_files_left_count
            # -1 needs for the last file
            completed = completed - 1 if completed > 0 else completed
            progress.update(decompressing, completed=completed)
            sleep(1)
