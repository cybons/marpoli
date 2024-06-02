import os
import re
from datetime import datetime, timedelta

from src.nn.slack_helper import SlackHelper


def extract_date_from_name(name):
    """
    名前からアンダーバーで囲まれた日付部分を抽出し、datetimeオブジェクトに変換します。
    正しくない日付形式の場合はNoneを返します。

    Args:
        name (str): ファイルまたはフォルダの名前

    Returns:
        datetime: 変換されたdatetimeオブジェクト、またはNone
    """
    match = re.search(r"_(\d{8})_", name)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            return None
    return None


def categorize_files_and_folders(directory):
    """
    指定されたディレクトリ内のファイルとフォルダを日付ごとに「今日」「明日」「それ以降」に分類します。

    Args:
        directory (str): ディレクトリのパス

    Returns:
        dict: カテゴリごとに分類されたファイル・フォルダの辞書
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    categorized = {"today": [], "tomorrow": [], "later": []}

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        date = extract_date_from_name(item)
        if date:
            if date.date() == today:
                categorized["today"].append(item_path)
            elif date.date() == tomorrow:
                categorized["tomorrow"].append(item_path)
            else:
                categorized["later"].append(item_path)

    return categorized


def create_slack_message(categorized):
    """
    カテゴリごとに分類されたファイル・フォルダをSlackのBlock Kitメッセージ形式に変換します。

    Args:
        categorized (dict): カテゴリごとに分類されたファイル・フォルダの辞書

    Returns:
        list: SlackのBlock Kit用のメッセージブロックのリスト
    """
    blocks = []

    for category, items in categorized.items():
        if items:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{category.capitalize()}*"},
                }
            )
            for item in items:
                blocks.append(
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"- {item}"}}
                )
            blocks.append({"type": "divider"})

    return blocks


# 使用例
if __name__ == "__main__":
    directory_path = r"/path/to/your/directory"  # 処理するディレクトリのパス
    slack_token = "your-slack-bot-token"  # Slackボットのトークン
    slack_channel = "#your-channel"  # 通知を送信するSlackチャンネル

    # ファイル・フォルダをカテゴリごとに分類
    categorized = categorize_files_and_folders(directory_path)

    # Slack用のメッセージブロックを作成
    blocks = create_slack_message(categorized)

    # Slackにメッセージを送信
    slack_helper = SlackHelper(token=slack_token)
    slack_helper.send_message(channel=slack_channel, blocks=blocks)
