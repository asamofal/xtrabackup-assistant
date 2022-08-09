from collections import UserList

from packaging import version
from rich.table import Table

from .backup import Backup
from utils import rprint


class BackupList(UserList):
    def __init__(self, xtrabackup_version: str):
        super().__init__()

        self._xtrabackup_version = xtrabackup_version

    def append(self, backup: Backup) -> None:
        if backup not in self and self._is_compatible(backup):
            super().append(backup)

        super().sort(key=lambda b: b.date, reverse=True)

    def extend(self, backups: list) -> None:
        for backup in backups:
            self.append(backup)

    def _is_compatible(self, backup: Backup) -> bool:
        return version.parse(backup.mysql_version) <= version.parse(self._xtrabackup_version)

    def print(self) -> None:
        title = f"Available backups (supported by Percona XtraBackup {self._xtrabackup_version})"
        table = Table(title=title)

        table.add_column('No')
        table.add_column('Source')
        table.add_column('Date', no_wrap=True)
        table.add_column('Filename', no_wrap=True)
        table.add_column('Size')

        for index, backup in enumerate(self):
            table.add_row(str(index + 1), backup.source, backup.date, backup.filename, backup.size)

        return rprint(table)

    @property
    def available_numbers(self) -> list:
        return [str(i) for i in range(1, len(self) + 1)]

    def __contains__(self, item: Backup) -> bool:
        duplicate = next((backup for backup in self.data if backup.filename == item.filename), None)

        return duplicate is not None
