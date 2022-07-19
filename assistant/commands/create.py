import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePath

from rich.progress import Progress, TextColumn, SpinnerColumn, BarColumn, TaskProgressColumn, DownloadColumn
from rich.text import Text

from assistant import XtrabackupMessage, SftpClient, Environment
from assistant.configs import Config
from utils import now, rprint


class CreateCommand:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config
        
        self._temp_backup_file_path = None
        self._temp_log_path = None
        self._archive_path = None

    def execute(self):
        self._create_backup()
        self._create_archive()

        rprint(Text.assemble(
            ('[Assistant] ', 'blue'),
            (f"[{now('%Y-%m-%d %H:%M:%S')}] ", 'default'),
            ('Backup successfully created: ', 'green3'),
            (f"{str(self._archive_path)} ", 'default italic'),
            (f"({self._archive_path.stat().st_size / float(1<<30):,.2f}GB)", 'default italic')
        ))

        # upload to SFTP backups storage if config provided
        if self._config.sftp is not None:
            self._upload_to_sftp_storage()

    def _create_backup(self) -> None:
        """ Create compressed dump (xbstream) with log file in temp dir """

        backup_timestamp = now('%Y-%m-%d_%H-%M')
        backup_file_name = f"{backup_timestamp}_{self._config.project}_{self._env.mysql_version}"
        temp_backup_file_path = Path(Config.TEMP_DIR_PATH, f"{backup_file_name}.xbstream")
        temp_log_path = Path(Config.TEMP_DIR_PATH, 'xtrabackup.log')

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
                f"--target-dir={Config.TEMP_DIR_PATH}"
            )
            command = subprocess.Popen(['xtrabackup', *command_options], stdout=backup_file, stderr=subprocess.PIPE)
            for line in command.stderr:
                message = XtrabackupMessage(str(line, 'utf-8'))

                log_file.write(f"{message.formatted}\n")
                rprint(f"[blue][ExtraBackup][/blue] {message.formatted}")

            return_code = command.wait()

        if return_code != 0:
            error_log_path = Path(Config.ERROR_LOG_DIR_PATH, f"{backup_timestamp}-error.log")
            shutil.move(temp_log_path, error_log_path)

            raise RuntimeError(f"Failed to create a backup! Error log: [default]{str(error_log_path)}")

        self._temp_backup_file_path = temp_backup_file_path
        self._temp_log_path = temp_log_path

    def _create_archive(self) -> None:
        """ Create a tarball for backup and log files """

        # prepare a directory for today's backups
        backup_archive_dir_path = Path(f"{Config.BACKUPS_PATH}/{now('%Y')}/{now('%m')}")
        if not os.path.exists(backup_archive_dir_path):
            os.makedirs(backup_archive_dir_path)

        # create an archive in the final dir
        backup_file_name = self._temp_backup_file_path.name.replace('xbstream', 'tar')
        backup_archive_path = Path(backup_archive_dir_path, backup_file_name)
        with Progress(
            TextColumn('[blue]\\[tar][/blue]'),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            transient=True
        ) as progress:
            rprint(f"[blue]\\[tar][/blue] [{now('%Y-%m-%d %H:%M:%S')}] Start creating archive.")

            try:
                with progress.open(
                        self._temp_backup_file_path, 'rb',
                        description='[blue]Creating archive...'
                ) as backup:
                    with tarfile.open(backup_archive_path, 'w') as tar:
                        # add backup file
                        file_info = tarfile.TarInfo(self._temp_backup_file_path.name)
                        file_info.size = self._temp_backup_file_path.stat().st_size
                        tar.addfile(file_info, fileobj=backup)
                        # add log file
                        tar.add(self._temp_log_path, arcname=self._temp_log_path.name)
                progress.stop()
            except KeyboardInterrupt:
                if os.path.exists(backup_archive_path):
                    os.remove(backup_archive_path)
                if len(os.listdir(backup_archive_dir_path)) == 0:
                    os.rmdir(backup_archive_path.parent)

                raise KeyboardInterrupt

            rprint(f"[blue]\\[tar][/blue] [{now('%Y-%m-%d %H:%M:%S')}] Archive created")

        self._archive_path = backup_archive_path

    def _upload_to_sftp_storage(self) -> None:
        """ Upload tarball to SFTP backups storage """

        with SftpClient(self._config.sftp) as sftp:
            rprint('[blue][SFTP][/blue] Connected to SFTP backups storage.')

            try:
                remote_path = PurePath(self._config.sftp.path, now('%Y'), now('%m'), self._archive_path.name)
                sftp.upload(self._archive_path, remote_path)
            except IOError as e:
                raise RuntimeError(f"Failed to upload the backup to SFTP backups storage: {e}")

            rprint('[blue][SFTP][/blue] [green3]Dump successfully uploaded to SFTP backups storage!')
