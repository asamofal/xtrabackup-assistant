class AssistantException(RuntimeError):
    pass


class ConfigError(AssistantException):
    pass


class SftpError(AssistantException):
    pass
