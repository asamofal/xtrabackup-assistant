import enum


class Command(enum.Enum):
    CREATE = 'create'
    CREATE_NO_UPLOAD = 'create_no_upload'
    RESTORE = 'restore'

    def __str__(self) -> str:
        return str(self.value)
