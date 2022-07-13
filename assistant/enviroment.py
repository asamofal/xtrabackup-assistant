import re
import subprocess

from utils.rich_print import rprint


class Environment:
    def __init__(self):
        self.mysql_version = self._get_mysql_server_version()
        self.xtrabackup_version = self._get_xtrabackup_version()

    def print_info(self) -> None:
        tool_versions = (
            f"[green3]Percona MySQL Server {self.mysql_version}",
            f"[green3]Percona XtraBackup {self.xtrabackup_version}"
        )
        rprint(f"[blue][Environment][/blue]", ' | '.join(tool_versions))

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
