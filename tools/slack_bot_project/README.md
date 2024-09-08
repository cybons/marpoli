```
/slack_bot_project
│
├── main.py  # メインスクリプト
├── config.py  # 設定ファイル（トークンやチャンネルIDなど）
├── requirements.txt  # 使用するライブラリの一覧
└── processors  # サブモジュールを格納するフォルダ
    ├── __init__.py  # パッケージとして認識させるためのファイル
    ├── task_list_processor.py  # :task_list: 絵文字の処理
    ├── important_tag_processor.py  # 重要なタグの処理
    └── custom_action_processor.py  # カスタムアクションの処理
```
