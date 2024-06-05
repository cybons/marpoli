import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import poll_module
import attendance_module
import safety_module

# 環境変数からトークンを取得
slack_token = os.getenv("SLACK_BOT_TOKEN")
app_token = os.getenv("SLACK_APP_TOKEN")

# Boltアプリのインスタンスを作成
app = App(token=slack_token)

# モジュールごとにハンドラーを登録
poll_module.register_poll_handlers(app)
attendance_module.register_attendance_handlers(app)
safety_module.register_safety_handlers(app)

# ソケットモードハンドラーを開始
if __name__ == "__main__":
    handler = SocketModeHandler(app, app_token)
    handler.start()