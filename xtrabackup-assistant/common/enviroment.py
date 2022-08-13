import re
import subprocess

from rich.text import Text

from utils import echo


class Environment:
    def __init__(self):
        self.mysql_version = self._get_mysql_server_version()
        self.xtrabackup_version = self._get_xtrabackup_version()

    def print_versions(self):
        echo(
            Text.assemble(
                (f"Percona MySQL Server {self.mysql_version}", 'green3'),
                (' | ', 'default'),
                (f"Percona XtraBackup {self.xtrabackup_version}", 'green3')
            ),
            author='Environment',
            time=False
        )

    @staticmethod
    def _get_mysql_server_version() -> str:
        try:
            command = subprocess.run(['mysql', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            mysql_server_about = command.stdout.decode('utf-8')
            mysql_server_version_match = re.search(r'Ver (\S+) for Linux', mysql_server_about)
            if mysql_server_version_match is None:
                raise RuntimeError('Percona MySQL Server version is not recognized!')
        except FileNotFoundError:
            raise RuntimeError('Percona MySQL Server is missing!')

        return mysql_server_version_match.group(1)

    @staticmethod
    def _get_xtrabackup_version() -> str:
        try:
            command = subprocess.run(['xtrabackup', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            xtrabackup_about = command.stdout.decode('utf-8')
            xtrabackup_version_match = re.search(r'xtrabackup version (\S+) based on MySQL server', xtrabackup_about)
            if xtrabackup_version_match is None:
                raise RuntimeError('XtraBackup tool version is not recognized!')
        except FileNotFoundError:
            raise RuntimeError('XtraBackup tool is missing!')

        return xtrabackup_version_match.group(1)
