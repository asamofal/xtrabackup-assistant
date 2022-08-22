from datetime import datetime
from operator import attrgetter

from dateutil.relativedelta import relativedelta

from common import Backup, BackupList
from configs import Config
from constants import BACKUPS_DIR_PATH


class RotateCommand:
    def __init__(self, config: Config):
        if config.rotation is None:
            raise RuntimeError("Required option 'rotation' is missing in the config")
        self._config = config

        self._backups_to_delete: BackupList = BackupList()

    def execute(self):
        local_backups_to_delete = self._rotate_local_backups()
        self._backups_to_delete.extend(local_backups_to_delete)

        self._backups_to_delete.print(title='Backups to be deleted')

    def _rotate_local_backups(self) -> BackupList:
        backups_to_delete = BackupList()

        backup_files = [
            Backup(source='local', path=path, size=path.stat().st_size) for path in BACKUPS_DIR_PATH.rglob('*.tar')
        ]
        # keep backups newer than N days
        pinned_backups_datetime = datetime.now() - relativedelta(days=self._config.rotation.keep_for_last_days)
        backups = [backup for backup in backup_files if backup.datetime < pinned_backups_datetime]

        # check by max store time
        obsolescence_datetime = datetime.now() - relativedelta(years=self._config.rotation.max_store_time_years)
        outdated_backups = [backup for backup in backups if backup.datetime < obsolescence_datetime]
        backups_to_delete.extend(outdated_backups)
        # remove outdated backups from the global list
        backups = list(set(backups) - set(outdated_backups))

        # group by year/month
        grouped_backups = {}
        for backup in backups:
            backup_year = backup.datetime.strftime('%Y')
            backup_month = backup.datetime.strftime('%m')

            # skip months connected to "pinned" period
            pinned_backups_year = pinned_backups_datetime.strftime('%Y')
            pinned_backups_month = pinned_backups_datetime.strftime('%m')
            if backup_year == pinned_backups_year and backup_month >= pinned_backups_month:
                continue

            if backup_year not in grouped_backups:
                grouped_backups[backup_year] = {}
            if backup_month not in grouped_backups[backup_year]:
                grouped_backups[backup_year][backup_month] = []

            grouped_backups[backup_year][backup_month].append(backup)

        # keep only one newest backup each month (except months connected to "pinned" period)
        for year in grouped_backups:
            for month in grouped_backups[year]:
                if len(grouped_backups[year][month]) > 1:
                    latest_backup = max(grouped_backups[year][month], key=attrgetter('datetime'))
                    redundant_month_backups = [
                        backup for backup in grouped_backups[year][month] if backup != latest_backup
                    ]
                    backups_to_delete.extend(redundant_month_backups)

        return backups_to_delete
