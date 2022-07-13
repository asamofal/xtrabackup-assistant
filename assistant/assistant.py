from pathlib import Path

from assistant.xtrabackup_message import XtrabackupMessage
from utils.time import now
import subprocess


class Assistant:
    def __init__(self, env: Environment, config: Config):
        self._env = env
        self._config = config

    def create(self) -> None:
        backup_timestamp = now('%Y-%m-%d_%H-%M')
        backup_file_name = f"{backup_timestamp}_inside_full_{self._env.mysql_version}"
        temp_backup_file_path = Path(TEMP_DIR_PATH, f"{backup_file_name}.xbstream")
        temp_log_path = Path(TEMP_DIR_PATH, 'xtrabackup.log')

        with open(temp_backup_file_path, 'wb') as backup_file, open(temp_log_path, 'w') as log_file:
            command_options = (
                '--backup',
                '--stream=xbstream',
                '--compress',
                f"--parallel={self._config.parallel}",
                '--compress-threads=5',
                f"--user={self._config.user}",
                f"--password={self._config.password}",
                '--host=127.0.0.1',
                f"--target-dir={TEMP_DIR_PATH}"
            )
            command = subprocess.Popen(['xtrabackup', *command_options], stdout=backup_file, stderr=subprocess.PIPE)
            for line in command.stderr:
                message = XtrabackupMessage(str(line, 'utf-8'))

                log_file.write(f"{message.formatted}\n")
                rprint(f"[blue][ExtraBackup][/blue] {message.formatted}")

            return_code = command.wait()

        if return_code != 0:
            log_path = Path(ERROR_LOG_DIR_PATH, f"{backup_timestamp}-error.log")
            shutil.move(temp_log_path, log_path)

            raise RuntimeError(f"Failed to create a backup! Error log: [default]{str(log_path)}")

        # prepare a directory for today's backups
        backup_archive_dir_path = Path(f"{BACKUPS_PATH}/{now('%Y')}/{now('%m')}")
        if not os.path.exists(backup_archive_dir_path):
            os.makedirs(backup_archive_dir_path)

        # make an archive in the final dir
        backup_archive_path = Path(backup_archive_dir_path, f"{backup_file_name}.tar")
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
                with progress.open(temp_backup_file_path, 'rb', description='[blue]Creating archive...') as backup:
                    with tarfile.open(backup_archive_path, 'w') as tar:
                        # add backup file
                        file_info = tarfile.TarInfo(temp_backup_file_path.name)
                        file_info.size = temp_backup_file_path.stat().st_size
                        tar.addfile(file_info, fileobj=backup)
                        # add log file
                        tar.add(temp_log_path, arcname=temp_log_path.name)
                progress.stop()
            except KeyboardInterrupt:
                if os.path.exists(backup_archive_path):
                    os.remove(backup_archive_path)
                if len(os.listdir(backup_archive_dir_path)) == 0:
                    os.rmdir(backup_archive_path.parent)

                raise KeyboardInterrupt

            rprint(f"[blue]\\[tar][/blue] [{now('%Y-%m-%d %H:%M:%S')}] Archive created.")

        backup_archive_size = backup_archive_path.stat().st_size
        success_message = (
            f"[blue][Assistant][/blue]",
            f"[{now('%Y-%m-%d %H:%M:%S')}]",
            f"[green3]Backup successfully created:[/green3]",
            f"[italic]{str(backup_archive_path)}",
            f"({backup_archive_size / float(1<<30):,.2f}GB)"
        )
        rprint(' '.join(success_message))

        # upload to SFTP backups storage if config provided
        if self._config.sftp is not None:
            with SftpClient(self._config.sftp) as sftp:
                rprint('[blue][SFTP][/blue] Connected to SFTP backups storage.')

                try:
                    remote_path = PurePath(self._config.sftp.path, now('%Y'), now('%m'), backup_archive_path.name)
                    sftp.upload(backup_archive_path, remote_path)
                except IOError as e:
                    raise RuntimeError(f"[SFTP] Failed to upload the backup to SFTP backups storage: {e}")

                rprint('[blue][SFTP][/blue] [green3]Dump successfully uploaded to SFTP backups storage!')

    def restore(self) -> None:
        pass

    @staticmethod
    def clear_temp_dir() -> None:
        with os.scandir(TEMP_DIR_PATH) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)

        version_check_log = f"/tmp/percona-version-check"
        if os.path.exists(version_check_log):
            os.remove(version_check_log)