import os
import sqlite3
from datetime import datetime, timedelta

from processors import important_tag_processor, task_list_processor
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slackクライアントの設定
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)
channel_id = "YOUR_CHANNEL_ID"

# SQLiteデータベースの設定
DB_FILE = "timestamps.db"


def init_db():
    """SQLiteデータベースの初期化"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # テーブルが存在しない場合は作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fetched_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def get_last_timestamp():
    """最新のタイムスタンプを取得"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) FROM fetched_messages")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else (datetime.now() - timedelta(hours=1)).timestamp()


def save_timestamp(timestamp):
    """タイムスタンプを保存"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO fetched_messages (timestamp) VALUES (?)", (timestamp,))
    conn.commit()
    conn.close()


def fetch_messages(client, channel_id):
    """メッセージを取得"""
    last_timestamp = get_last_timestamp()
    now = datetime.now()

    try:
        response = client.conversations_history(
            channel=channel_id,
            oldest=last_timestamp,
            latest=now.timestamp(),
            inclusive=False,  # 最新タイムスタンプを含まない
            limit=100,
        )
        return response["messages"]
    except SlackApiError as e:
        print(f"Error fetching conversations: {e.response['error']}")
        return []


def process_message(message):
    """メッセージを処理"""
    text = message.get("text", "")

    if ":task_list:" in text:
        task_list_processor.process(message)
    elif "#重要" in text:
        important_tag_processor.process(message)
    # 追加の処理条件もここに追加できます


def main():
    # データベースの初期化
    init_db()

    # メッセージを取得して処理
    messages = fetch_messages(client, channel_id)
    for message in messages:
        process_message(message)

    # 最新のメッセージのタイムスタンプを保存
    if messages:
        latest_message_timestamp = max(float(message["ts"]) for message in messages)
        save_timestamp(latest_message_timestamp)


if __name__ == "__main__":
    main()
