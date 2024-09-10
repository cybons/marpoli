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
DB_FILE = "items.db"

def init_db():
    """SQLiteデータベースの初期化"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # itemsテーブルの作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY,  -- item_idをユニークなプライマリキーとする
        subject TEXT,
        deadline TEXT,
        url TEXT,
        priority TEXT,
        status TEXT
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
    """Slackチャンネルからメッセージを取得"""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    try:
        response = client.conversations_history(
            channel=channel_id,
            oldest=one_hour_ago.timestamp(),
            latest=now.timestamp(),
            inclusive=True,
            limit=100,
        )
        return response["messages"]
    except SlackApiError as e:
        print(f"Error fetching conversations: {e.response['error']}")
        return []

def upsert_item(item):
    """アイテムを挿入または更新し、変更があれば変更内容を返す"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 既存データの取得
    cursor.execute("SELECT * FROM items WHERE item_id = ?", (item['item_id'],))
    existing_item = cursor.fetchone()

    if existing_item:
        # 変更をチェック
        changes = {}
        columns = ['subject', 'deadline', 'url', 'priority', 'status']
        for i, col in enumerate(columns, start=1):
            if item[col] != existing_item[i]:
                changes[col] = {'old': existing_item[i], 'new': item[col]}

        # データが異なる場合のみ更新
        if changes:
            cursor.execute("""
                UPDATE items SET subject = ?, deadline = ?, url = ?, priority = ?, status = ?
                WHERE item_id = ?
            """, (item['subject'], item['deadline'], item['url'], item['priority'], item['status'], item['item_id']))
            conn.commit()
        
        conn.close()
        return changes  # 変更点を返す
    else:
        # 新規データの挿入
        cursor.execute("""
            INSERT INTO items (item_id, subject, deadline, url, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item['item_id'], item['subject'], item['deadline'], item['url'], item['priority'], item['status']))
        conn.commit()
        conn.close()
        return None  # 新規挿入の場合は変更なし

def process_message(message):
    """メッセージを処理し、データベースに挿入・更新"""
    text = message.get("text", "")

    # 正規表現でsubject, item_id, deadline, url, priority, statusをパースする（例）
    parsed_data = {
        'item_id': 'example_id',  # パースされたデータ
        'subject': 'example_subject',
        'deadline': '2024-09-30',
        'url': 'https://example.com',
        'priority': 'high',
        'status': 'in-progress'
    }

    changes = upsert_item(parsed_data)
    if changes:
        print(f"Updated item with changes: {changes}")

def main():
    # データベースの初期化
    init_db()

    # メッセージを取得して処理
    messages = fetch_messages(client, channel_id)
    for message in messages:
        process_message(message)

if __name__ == "__main__":
    main()