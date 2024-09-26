import os
import time
import pickle
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack APIトークンを環境変数から取得（Botトークンを使用）
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

# 無視するユーザーのリスト（依頼元のユーザーIDを含める）
ignored_user_ids = ['USER_ID_1', 'USER_ID_2']  # 無視したいユーザーIDを追加

# メンションするユーザーのリスト
mention_user_ids = ['USER_ID_3', 'USER_ID_4']  # メンションしたいユーザーIDを追加

# リマインド除外とする絵文字のリスト
exclude_reactions = ['ok', 'white_check_mark', 'check']  # 除外したい絵文字の名前を追加

# チェックするチャンネルIDを指定
channel_id = 'YOUR_CHANNEL_ID'

# あなたのSlackワークスペースのドメイン名を設定
workspace_domain = 'your_workspace_domain'  # 例: 'myworkspace'

# リマインドしたメッセージの情報を保持するファイルのパス
pickle_file = 'reminded_messages.pkl'

# リマインドしたメッセージの情報を保持
if os.path.exists(pickle_file):
    with open(pickle_file, 'rb') as f:
        reminded_messages = pickle.load(f)
else:
    reminded_messages = {}

def save_reminded_messages():
    with open(pickle_file, 'wb') as f:
        pickle.dump(reminded_messages, f)

def check_messages():
    try:
        # 自分（アプリ自身）のユーザーIDを取得
        auth_response = client.auth_test()
        bot_user_id = auth_response['user_id']

        # チャンネルのメッセージ履歴を取得（最新の100件）
        response = client.conversations_history(channel=channel_id, limit=100)
        messages = response['messages']

        for message in messages:
            ts = message['ts']
            user = message.get('user')

            # アプリ自身が送信したメッセージはスキップ
            if user == bot_user_id:
                continue

            # 無視するユーザーからのメッセージはスキップ
            if user in ignored_user_ids:
                continue

            # リマインド情報を取得
            reminder_info = reminded_messages.get(ts, {'count': 0, 'last_reminded': datetime.min, 'reminder_ts': None})

            # 元のメッセージにexclude_reactionsが付いているかチェック
            try:
                original_reactions_response = client.reactions_get(channel=channel_id, timestamp=ts)
                original_reactions = original_reactions_response.get('message', {}).get('reactions', [])
                has_exclude_reaction_on_original = any(reaction['name'] in exclude_reactions for reaction in original_reactions)
            except SlackApiError as e:
                print(f"Error getting reactions for original message: {e.response['error']}")
                has_exclude_reaction_on_original = False

            if has_exclude_reaction_on_original:
                # リマインドメッセージを削除
                if reminder_info['reminder_ts']:
                    try:
                        client.chat_delete(channel=channel_id, ts=reminder_info['reminder_ts'])
                    except SlackApiError as e:
                        print(f"Error deleting reminder message: {e.response['error']}")
                # リマインド情報を削除
                if ts in reminded_messages:
                    del reminded_messages[ts]
                continue  # 次のメッセージへ

            # リマインドメッセージがある場合
            if reminder_info['reminder_ts']:
                # リマインドメッセージにexclude_reactionsが付いているかチェック
                try:
                    reminder_reactions_response = client.reactions_get(channel=channel_id, timestamp=reminder_info['reminder_ts'])
                    reminder_reactions = reminder_reactions_response.get('message', {}).get('reactions', [])
                    exclude_reactions_on_reminder = [reaction['name'] for reaction in reminder_reactions if reaction['name'] in exclude_reactions]
                except SlackApiError as e:
                    print(f"Error getting reactions for reminder message: {e.response['error']}")
                    exclude_reactions_on_reminder = []

                if exclude_reactions_on_reminder:
                    # 元のメッセージに同じリアクションを追加
                    for reaction_name in exclude_reactions_on_reminder:
                        try:
                            client.reactions_add(name=reaction_name, channel=channel_id, timestamp=ts)
                        except SlackApiError as e:
                            if e.response['error'] != 'already_reacted':
                                print(f"Error adding reaction to original message: {e.response['error']}")
                    # リマインドメッセージを削除
                    try:
                        client.chat_delete(channel=channel_id, ts=reminder_info['reminder_ts'])
                    except SlackApiError as e:
                        print(f"Error deleting reminder message: {e.response['error']}")
                    # リマインド情報を削除
                    if ts in reminded_messages:
                        del reminded_messages[ts]
                    continue  # 次のメッセージへ

            # スレッドの返信の有無をチェック
            reply_count = int(message.get('reply_count', 0))
            if reply_count > 0:
                continue

            # 最大リマインド回数を設定（例：3回）
            if reminder_info['count'] >= 3:
                continue

            # 最後にリマインドした時間からの経過時間を計算
            time_since_last_reminder = datetime.now() - reminder_info['last_reminded']

            # リマインド間隔を設定（例：1時間）
            if time_since_last_reminder >= timedelta(hours=1):
                # 前回のリマインドメッセージを削除
                if reminder_info['reminder_ts']:
                    try:
                        client.chat_delete(
                            channel=channel_id,
                            ts=reminder_info['reminder_ts']
                        )
                    except SlackApiError as e:
                        print(f"Error deleting previous reminder message: {e.response['error']}")

                # メッセージリンクを生成
                formatted_ts = ts.replace('.', '')
                message_link = f"https://{workspace_domain}.slack.com/archives/{channel_id}/p{formatted_ts}"

                # メンションするユーザーをテキストに追加
                mention_text = ' '.join([f'<@{user_id}>' for user_id in mention_user_ids])

                # リマインドメッセージを作成
                reminder_text = f"{mention_text}\n未対応のメッセージがあります: <{message_link}|こちらを確認してください>"

                # リマインドメッセージをチャンネルに投稿
                reminder_response = client.chat_postMessage(
                    channel=channel_id,
                    text=reminder_text
                )

                # リマインド情報を更新
                reminded_messages[ts] = {
                    'count': reminder_info['count'] + 1,
                    'last_reminded': datetime.now(),
                    'reminder_ts': reminder_response['ts']  # リマインドメッセージのタイムスタンプを保存
                }

        # リマインド情報を保存
        save_reminded_messages()

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

if __name__ == "__main__":
    check_messages()