from collections import UserList
from typing import Union

from packaging.version import Version
from rich.table import Table

from utils import echo
from .backup import Backup


class BackupList(UserList):
    def __init__(self, init_list: list = None, xtrabackup_version: Union[str, None] = None):
        super().__init__()

        self._xtrabackup_version = xtrabackup_version

        if init_list is not None:
            self.extend(init_list)

    def append(self, backup: Backup) -> None:
        if backup not in self and self._is_compatible(backup):
            super().append(backup)

        super().sort(key=lambda b: b.date, reverse=True)

    def extend(self, backups: Union[list, 'BackupList']) -> None:
        for backup in backups:
            self.append(backup)

    def _is_compatible(self, backup: Backup) -> bool:
        if self._xtrabackup_version is None:
            return True

        mysql_version = Version(backup.mysql_version)
        xtrabackup_version = Version(self._xtrabackup_version)

        # With the release of Percona XtraBackup 8.0.34-29,
        # Percona XtraBackup allows backups on version 8.0.35 and higher
        if xtrabackup_version >= Version('8.0.34-29') and (mysql_version.major == 8 and mysql_version.minor == 0):
            return True

        return mysql_version <= xtrabackup_version

    def print(self, title: str = '') -> None:
        table = Table(title=title)

        table.add_column('No')
        table.add_column('Source')
        table.add_column('Date', no_wrap=True)
        table.add_column('Filename', no_wrap=True)
        table.add_column('Size')

        for index, backup in enumerate(self):
            table.add_row(str(index + 1), backup.source, backup.date, backup.filename, backup.size)

        return echo(table)

    @property
    def available_numbers(self) -> list:
        return [str(i) for i in range(1, len(self) + 1)]

    def __contains__(self, item: Backup) -> bool:
        duplicate = next((backup for backup in self.data if backup.filename == item.filename), None)

        return duplicate is not None
