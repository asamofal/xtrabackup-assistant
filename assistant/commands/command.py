import enum


class Command(enum.Enum):
    CREATE = 'create'
    RESTORE = 'restore'

    def __str__(self) -> str:
        return str(self.value)
