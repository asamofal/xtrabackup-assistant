from datetime import datetime
from pathlib import PurePath

from humanize import naturalsize


class Backup:
    def __init__(self, source: str, path: PurePath, size: int):
        self.source = source
        self.path = path
        self.size = naturalsize(size)

    @property
    def date(self) -> str:
        return datetime.strptime(self.filename.split('_')[0], '%Y-%m-%d-%H-%M').strftime('%Y-%m-%d %H:%M')

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def mysql_version(self) -> str:
        return self.path.stem.split('_')[-1]
