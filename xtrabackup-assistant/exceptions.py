class AssistantException(Exception):
    pass


class ConfigError(AssistantException):
    pass


class SftpError(AssistantException):
    pass
