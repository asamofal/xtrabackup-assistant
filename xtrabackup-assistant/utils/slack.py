import slack_notifications as slack
from rich.text import Text

from configs import SlackConfig


class Slack:
    def __init__(self, slack_config: SlackConfig):
        self._config = slack_config

        self._slack = slack.Slack(slack_config.token)

    def notify(self, project: str, error: Exception):
        attachment = slack.Attachment(
            title='XtraBackup Assistant error!',
            text=str(Text.from_markup(str(error))),
            footer=project,
            color='red',
        )
        self._slack.send_notify(channel=self._config.channel, attachments=[attachment])
