import enum


class Command(enum.Enum):
    CREATE = 'create'
    CREATE_UPLOAD = 'create_upload'
    RESTORE = 'restore'
    ROTATE = 'rotate'

    def __str__(self) -> str:
        return str(self.value)
