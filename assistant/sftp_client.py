import socket
import stat
from pathlib import Path, PurePath
from re import Pattern

import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, DownloadColumn, TransferSpeedColumn

from assistant.configs.sftp_config import SftpConfig
from utils.rich_print import rprint


class SftpClient:
    def __init__(self, config: SftpConfig):
        try:
            self._config = config

            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(hostname=config.host, username=config.user, password=config.password)
            self.sftp_client = self.ssh_client.open_sftp()
        except (SSHException, AuthenticationException, socket.error) as e:
            raise RuntimeError(f"Failed to init the SFTP connection: {e}")

    def upload(self, local_path: Path, remote_path: PurePath, display_progress=True):
        remote_dir_path = PurePath(str(remote_path.parent).lstrip('/'))
        self.mkdir_p(remote_dir_path)

        try:
            if display_progress:
                with Progress(
                    TextColumn('[blue][SFTP][/blue]'),
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    transient=True
                ) as progress:
                    file_size = local_path.stat().st_size
                    uploading = progress.add_task("[blue]Uploading...", total=file_size)

                    self.sftp_client.put(
                        str(local_path),
                        str(remote_path),
                        lambda transferred, total: progress.update(uploading, completed=transferred)
                    )
            else:
                self.sftp_client.put(str(local_path), str(remote_path))
        except (EOFError, SSHException, KeyboardInterrupt):
            self.close()

            rprint('[blue][SFTP][/blue] [italic]Terminate signal received. Cleaning up....')
            # create a new connection as a socket of the current is closed already
            with SftpClient(self._config) as sftp:
                sftp.delete(remote_path, ignore_errors=True)
                if len(sftp.sftp_client.listdir(str(remote_path.parent))) == 0:
                    sftp.delete(remote_path.parent, ignore_errors=True)

                raise KeyboardInterrupt

    def delete(self, remote_path: PurePath, ignore_errors=False):
        try:
            path = str(remote_path)
            is_dir = stat.S_ISDIR(self.sftp_client.stat(path).st_mode)
            self.sftp_client.rmdir(path) if is_dir else self.sftp_client.remove(path)
        except IOError as e:
            if ignore_errors is False:
                raise e

    def mkdir_p(self, remote_path: PurePath):
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

        for entry in self.sftp_client.listdir_attr(str(remote_path)):
            is_dir = stat.S_ISDIR(entry.st_mode)
            if is_dir:
                file_paths += self.r_find_files(PurePath(remote_path, entry.filename), pattern)
            elif pattern is None or pattern.search(entry.filename):
                file_paths.append(PurePath(remote_path, entry.filename))

        return file_paths

    def close(self):
        if self.sftp_client is not None:
            self.sftp_client.close()

        if self.ssh_client is not None:
            self.ssh_client.close()

    def __enter__(self) -> "SftpClient":
        return self

    def __exit__(self, e_type, value, traceback):
        self.close()
