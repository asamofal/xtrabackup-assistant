import os
import shutil
from pathlib import Path


def clear_dir(dir_path: Path) -> None:
    with os.scandir(str(dir_path)) as entries:
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry.path)
            elif entry.name != '.gitignore':
                os.remove(entry.path)
