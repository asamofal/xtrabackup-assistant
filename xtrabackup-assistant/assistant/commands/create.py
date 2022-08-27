import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePath
from typing import Union

from rich.progress import Progress, TextColumn, SpinnerColumn, BarColumn, TaskProgressColumn, DownloadColumn
from rich.text import Text

from common import Environment, XtrabackupMessage, Backup
from configs import Config
from constants import BACKUPS_DIR_PATH, TEMP_DIR_PATH, ERROR_LOG_DIR_PATH
from utils import now, Sftp, echo, echo_warning, logger


class CreateCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

        self._temp_backup_file_path = None
        self._temp_log_path = None
        self._backup: Union[Backup, None] = None

    def execute(self, upload: bool = True) -> None:
        self._create_backup()
        self._create_archive()

        success_msg = Text.assemble(
            ('Backup successfully created: ', 'green3'),
            (f"{self._backup.filename} ", 'default italic'),
            (f"({self._backup.size})", 'default italic')
        )
        echo(success_msg, time=False)

        if upload:
            if self._config.sftp is not None:
                self._upload_to_sftp_storage()
                echo('Dump successfully uploaded to SFTP backups storage!', style='green3', author='SFTP')
                logger.info(Text.from_markup(str(success_msg.append('. Uploaded to SFTP storage.'))))
            else:
                echo_warning("'sftp' option is missing in the config. Upload is skipped.")
        else:
            logger.info(Text.from_markup(str(success_msg)))

    def _create_backup(self) -> None:
        """ Create compressed dump (xbstream) with log file in temp dir """

        backup_timestamp = now('%Y-%m-%d-%H-%M')
        backup_file_name = f"{backup_timestamp}_{self._config.project_name}_{self._env.mysql_version}"
        temp_backup_file_path = Path(TEMP_DIR_PATH, f"{backup_file_name}.xbstream")
        temp_log_path = Path(TEMP_DIR_PATH, 'xtrabackup.log')

        with open(temp_backup_file_path, 'wb') as backup_file, open(temp_log_path, 'w') as log_file:
            command_options = (
                '--backup',
                '--stream=xbstream',
                '--compress',
                f"--parallel={self._config.xtrabackup.parallel}",
                '--compress-threads=5',
                f"--user={self._config.xtrabackup.user}",
                f"--password={self._config.xtrabackup.password}",
                '--host=127.0.0.1',
                f"--target-dir={TEMP_DIR_PATH}"
            )
            command = subprocess.Popen(['xtrabackup', *command_options], stdout=backup_file, stderr=subprocess.PIPE)
            for line in command.stderr:
                message = XtrabackupMessage(str(line, 'utf-8'))

                log_file.write(f"{message.formatted}\n")
                echo(message.formatted, author='XtraBackup', time=False)

            return_code = command.wait()

        if return_code != 0:
            error_log_path = Path(ERROR_LOG_DIR_PATH, f"{backup_timestamp}-error.log")
            shutil.move(temp_log_path, error_log_path)

            raise RuntimeError(f"Failed to create a backup! Error log: [default]{str(error_log_path)}")

        self._temp_backup_file_path = temp_backup_file_path
        self._temp_log_path = temp_log_path

    def _create_archive(self) -> None:
        """ Create a tarball for backup and log files """

        # prepare a directory for today's backups
        backup_archive_dir_path = Path(f"{BACKUPS_DIR_PATH}/{now('%Y')}/{now('%m')}")
        if not os.path.exists(backup_archive_dir_path):
            os.makedirs(backup_archive_dir_path)

        # create an archive in the final dir
        backup_file_name = self._temp_backup_file_path.name.replace('xbstream', 'tar')
        backup_archive_path = Path(backup_archive_dir_path, backup_file_name)
        with Progress(
            TextColumn('[blue]\\[tar][/blue]'),
            SpinnerColumn(),
            TextColumn('[blue]Creating archive...'),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            transient=True
        ) as progress:
            echo('Start creating archive', author='tar')

            try:
                with progress.open(self._temp_backup_file_path, 'rb',) as backup:
                    with tarfile.open(backup_archive_path, 'w') as tar:
                        # add backup file
                        file_info = tarfile.TarInfo(self._temp_backup_file_path.name)
                        file_info.size = self._temp_backup_file_path.stat().st_size
                        tar.addfile(file_info, fileobj=backup)
                        # add log file
                        tar.add(self._temp_log_path, arcname=self._temp_log_path.name)
            except KeyboardInterrupt:
                if os.path.exists(backup_archive_path):
                    os.remove(backup_archive_path)
                if len(os.listdir(backup_archive_dir_path)) == 0:
                    os.rmdir(backup_archive_path.parent)
                raise

            progress.stop()

            echo('Archive created', author='tar')

        self._backup = Backup(source='local', path=backup_archive_path, size=backup_archive_path.stat().st_size)

    def _upload_to_sftp_storage(self) -> None:
        """ Upload tarball to SFTP backups storage """

        with Sftp(self._config.sftp) as sftp:
            echo('Connected to SFTP backups storage.', author='SFTP')

            try:
                remote_path = PurePath(self._config.sftp.path, now('%Y'), now('%m'), self._backup.filename)
                sftp.upload(Path(self._backup.path), remote_path)
            except IOError as e:
                raise RuntimeError(f"Failed to upload the backup to SFTP backups storage: {e}")
