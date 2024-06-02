from enum import Enum

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackChannel(Enum):
    GENERAL = "general"
    RANDOM = "random"
    DEVELOPMENT = "development"


class SlackHelper:
    def __init__(self, token):
        """
        SlackHelperクラスのコンストラクタ。

        Args:
            token (str): Slack APIの認証トークン
        """
        self.client = WebClient(token=token)

    def send_message(
        self, channel: SlackChannel, text: str | None = None, blocks: str | None = None
    ):
        """
        Slackチャンネルにメッセージを送信します。

        Args:
            channel (str): メッセージを送信するSlackチャンネル
            text (str, optional): 送信するテキストメッセージ。ブロックが指定されている場合は無視されます。
            blocks (list, optional): 送信するBlock Kitメッセージのリスト

        Returns:
            dict: Slack APIのレスポンス
        """
        try:
            if blocks:
                response = self.client.chat_postMessage(
                    channel=channel.value, blocks=blocks
                )
            else:
                response = self.client.chat_postMessage(
                    channel=channel.value, text=text
                )
            return response
        except SlackApiError as e:
            print(f"Error posting to Slack: {e.response['error']}")
            return None
