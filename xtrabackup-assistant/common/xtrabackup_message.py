import re
from datetime import datetime


class XtrabackupMessage:
    def __init__(self, message: str):
        self.original = message
        self.formatted = self._format()

    def _format(self) -> str:
        message = self.original.split()

        # format timestamp if this is ISO 8601 date at start
        try:
            message[0] = f"[{datetime.fromisoformat(message[0]).strftime('%Y-%m-%d %H:%M:%S')}]"
        except ValueError:
            # format timestamp if it's 'version_check' utility date at start
            version_check_timestamp = re.match(r'\d{6} \d{2}:\d{2}:\d{2}', self.original)
            if version_check_timestamp is not None:
                timestamp = datetime.strptime(version_check_timestamp.group(), '%y%m%d %H:%M:%S')
                message[0:2] = [f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}]"]

        return ' '.join(message)
