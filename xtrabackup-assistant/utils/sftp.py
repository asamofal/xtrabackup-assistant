import socket
import stat
from pathlib import Path, PurePath
from re import Pattern

import paramiko
from paramiko.sftp import SFTPError
from paramiko.ssh_exception import SSHException
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, DownloadColumn, TransferSpeedColumn

from configs import SftpConfig
from utils import echo


class Sftp:
    def __init__(self, config: SftpConfig):
        try:
            self._config = config

            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(hostname=config.host, username=config.user, password=config.password, timeout=10)
            self.sftp_client = self.ssh_client.open_sftp()
        except (SSHException, socket.error) as e:
            raise RuntimeError(f"Failed to init the SFTP connection: {e}")

    def download(self, remote_path: PurePath, local_path: Path, display_progress=True):
        if not local_path.parent.exists():
            local_path.parent.mkdir(parents=True)

        try:
            if display_progress:
                with Progress(
                    TextColumn('[blue][SFTP][/blue]'),
                    SpinnerColumn(),
                    TextColumn('[progress.description]{task.description}'),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    transient=True
                ) as progress:
                    file_size = self.sftp_client.stat(str(remote_path)).st_size
                    downloading = progress.add_task('[blue]Downloading...', total=file_size)

                    self.sftp_client.get(
                        str(remote_path),
                        str(local_path),
                        lambda transferred, total: progress.update(downloading, completed=transferred)
                    )
            else:
                self.sftp_client.get(str(remote_path), str(local_path))
        except (EOFError, SSHException, SFTPError, KeyboardInterrupt) as e:
            echo('Error or terminate signal received. Cleaning up....', style='italic', author='SFTP')

            self.close()

            local_path.unlink()
            if not any(local_path.parent.iterdir()):
                local_path.parent.rmdir()

            if isinstance(e, KeyboardInterrupt):
                raise
            else:
                raise RuntimeError(f'SFTP download failed: {e}')

    def upload(self, local_path: Path, remote_path: PurePath, display_progress=True):
        remote_dir_path = PurePath(str(remote_path.parent).lstrip('/'))
        self._mkdir_p(remote_dir_path)

        try:
            if display_progress:
                with Progress(
                    TextColumn('[blue][SFTP][/blue]'),
                    SpinnerColumn(),
                    TextColumn('[progress.description]{task.description}'),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    transient=True
                ) as progress:
                    file_size = local_path.stat().st_size
                    uploading = progress.add_task('[blue]Uploading...', total=file_size)

                    self.sftp_client.put(
                        str(local_path),
                        str(remote_path),
                        lambda transferred, total: progress.update(uploading, completed=transferred)
                    )
            else:
                self.sftp_client.put(str(local_path), str(remote_path))
        except (EOFError, SSHException, KeyboardInterrupt) as e:
            echo('Error or terminate signal received. Cleaning up....', style='italic', author='SFTP')

            self.close()

            # create a new connection as a socket of the current is closed already
            with Sftp(self._config) as sftp:
                sftp.delete(remote_path, ignore_errors=True)
                if len(sftp.sftp_client.listdir(str(remote_path.parent))) == 0:
                    sftp.delete(remote_path.parent, ignore_errors=True)

            if isinstance(e, KeyboardInterrupt):
                raise
            else:
                raise RuntimeError(f'SFTP upload failed: {e}')

    def delete(self, remote_path: PurePath, ignore_errors=False):
        try:
            path = str(remote_path)
            is_dir = stat.S_ISDIR(self.sftp_client.stat(path).st_mode)
            self.sftp_client.rmdir(path) if is_dir else self.sftp_client.remove(path)
        except IOError:
            if ignore_errors is False:
                raise

    def _mkdir_p(self, remote_path: PurePath):
        """Make parent directories as needed"""
        dir_path = ''
        for dir_name in remote_path.parts:
            dir_path += f"/{dir_name}"
            try:
                self.sftp_client.listdir(dir_path)
            except IOError:
                self.sftp_client.mkdir(dir_path, 0o755)

    def r_find_files(self, remote_path: PurePath, pattern: Pattern = None) -> list:
        file_paths = []

        try:
            for entry_attr in self.sftp_client.listdir_attr(str(remote_path)):
                is_dir = stat.S_ISDIR(entry_attr.st_mode)
                if is_dir:
                    file_paths += self.r_find_files(PurePath(remote_path, entry_attr.filename), pattern)
                elif pattern is None or pattern.search(entry_attr.filename):
                    file_paths.append({
                        'path': PurePath(remote_path, entry_attr.filename),
                        'attr': entry_attr
                    })
        except IOError:
            # in case of a wrong remote path just return an empty list
            pass

        return file_paths

    def close(self):
        if self.sftp_client is not None:
            self.sftp_client.close()

        if self.ssh_client is not None:
            self.ssh_client.close()

    def __enter__(self) -> "Sftp":
        return self

    def __exit__(self, e_type, value, traceback):
        self.close()
