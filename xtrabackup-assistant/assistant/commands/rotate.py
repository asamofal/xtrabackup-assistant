import re
from datetime import datetime
from operator import attrgetter

from dateutil.relativedelta import relativedelta

from common import Backup, BackupList
from configs import Config
from constants import BACKUPS_DIR_PATH
from utils import Sftp, rotation_logger, echo


class RotateCommand:
    def __init__(self, config: Config):
        if config.rotation is None:
            raise RuntimeError("Required option 'rotation' is missing in the config")
        self._config = config

    def execute(self):
        self._rotate_local_backups()

        if self._config.sftp is not None:
            self._rotate_sftp_backups()

    def _rotate_local_backups(self) -> None:
        echo('Start local storage rotation')
        rotation_logger.info('Start LOCAL storage rotation')

        local_backups = [
            Backup(source='local', path=path, size=path.stat().st_size) for path in BACKUPS_DIR_PATH.rglob('*.tar')
        ]
        pinned_backups_datetime = datetime.now() - relativedelta(days=self._config.rotation.keep_for_last_days)

        backups_to_delete = BackupList(
            [backup for backup in local_backups if backup.datetime < pinned_backups_datetime]
        )

        for backup in backups_to_delete:
            backup.path.unlink()

            msg = f'Local backup deleted: {backup.filename}'
            echo(msg)
            rotation_logger.info(msg)

            # delete month dir if empty
            month_dir_path = backup.path.parent
            if not any(month_dir_path.iterdir()):
                month_dir_path.rmdir()

                msg = f'Local empty month dir deleted: {month_dir_path}'
                echo(msg)
                rotation_logger.info(msg)

            # delete year dir if empty
            year_dir_path = month_dir_path.parent
            if not any(year_dir_path.iterdir()):
                year_dir_path.rmdir()

                msg = f'Local empty year dir deleted: {year_dir_path}'
                echo(msg)
                rotation_logger.info(msg)

        echo('End local storage rotation')
        rotation_logger.info('End LOCAL storage rotation')

    def _rotate_sftp_backups(self) -> None:
        echo('Start sftp storage rotation')
        rotation_logger.info('Start SFTP storage rotation')

        with Sftp(self._config.sftp) as sftp:
            backups_to_delete = []

            remote_path = self._config.sftp.path
            backup_files = sftp.r_find_files(remote_path, re.compile('.tar$'))
            backups = [Backup(source='sftp', path=file['path'], size=file['attr'].st_size) for file in backup_files]

            # keep backups newer than N days
            current_day_start = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
            pinned_backups_datetime = current_day_start - relativedelta(days=self._config.rotation.keep_for_last_days)
            backups = [backup for backup in backups if backup.datetime < pinned_backups_datetime]

            # remove everything else in pinned month
            pinned_month = pinned_backups_datetime.strftime('%m')
            outdated_in_pinned_month = [
                backup for backup in backups if backup.datetime.strftime('%m') == pinned_month
            ]
            backups_to_delete.extend(outdated_in_pinned_month)
            backups = list(set(backups) - set(outdated_in_pinned_month))

            # check by max store time
            obsolescence_datetime = current_day_start - relativedelta(years=self._config.rotation.max_store_time_years)
            outdated_backups = [backup for backup in backups if backup.datetime < obsolescence_datetime]
            backups_to_delete.extend(outdated_backups)
            backups = list(set(backups) - set(outdated_backups))

            # group by year/month
            grouped_backups = {}
            for backup in backups:
                backup_year = backup.datetime.strftime('%Y')
                backup_month = backup.datetime.strftime('%m')

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

            for backup in backups_to_delete:
                try:
                    sftp.delete(backup.path)
                    msg = f'SFTP backup deleted: {backup.filename}'
                    echo(msg)
                    rotation_logger.info(msg)

                    # delete month dir if empty
                    month_dir_path = backup.path.parent
                    if not any(sftp.sftp_client.listdir(str(month_dir_path))):
                        sftp.delete(month_dir_path)
                        msg = f'SFTP empty month dir deleted: {month_dir_path}'
                        echo(msg)
                        rotation_logger.info(msg)

                    # delete year dir if empty
                    year_dir_path = month_dir_path.parent
                    if not any(sftp.sftp_client.listdir(str(year_dir_path))):
                        sftp.delete(year_dir_path)
                        msg = f'SFTP empty year dir deleted: {year_dir_path}'
                        echo(msg)
                        rotation_logger.info(msg)
                except IOError as e:
                    raise RuntimeError(f'Failed to delete SFTP entity: {e}')

        echo('End sftp storage rotation')
        rotation_logger.info('End SFTP storage rotation\n')
