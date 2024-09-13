import os
import pickle

import google.auth.transport.requests
import gspread
import pandas as pd
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Sheets APIの認証情報を設定
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# スクリプトのディレクトリを基準にパスを設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "",
)
TOKEN_FILE = os.path.join(BASE_DIR, "token.pickle")


# スプレッドシートIDと書き込む範囲
SPREADSHEET_ID = ""
SHEET_NAME = "シート1"
RANGE_NAME = "A:D"


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # トークンが存在しないか有効期限切れの場合、新しいトークンを取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(google.auth.transport.requests.Request())
            except RefreshError:
                print("リフレッシュトークンが無効です。再認証が必要です。")
                creds = get_new_credentials()
        else:
            creds = get_new_credentials()

        # 新しいトークンを保存
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds


def get_new_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


credentials = authenticate()
# gspreadでGoogleスプレッドシートにアクセス
gc = gspread.authorize(credentials)

# スプレッドシートのデータを取得
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
data = worksheet.get(RANGE_NAME)

# pandasのデータフレームに変換
df = pd.DataFrame(data[1:], columns=data[0])  # 最初の行をヘッダーとして使用

# データフレームを表示
print(df)
# 4列目にスラッシュが入っているかチェックし、新しい列を追加
# NoneまたはNaNを考慮して新しい列を追加
df["新しい列"] = df.iloc[:, 3].apply(
    lambda x: "〇" if x is not None and "/" in x else ""
)

# 新しい列のデータだけを書き戻す
new_column_data = df["新しい列"].tolist()

# 書き戻す範囲（例: "F2:F" + str(len(new_column_data) + 1)）
update_range = f"E2:F{len(new_column_data) + 1}"  # 例として6列目に書き戻す

# データを書き戻す
worksheet.update(update_range, [[cell] for cell in new_column_data])

print("スプレッドシートへの書き戻しが完了しました。")
