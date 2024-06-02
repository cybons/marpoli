import datetime
import os
import pickle

import google.auth.transport.requests
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OAuth 2.0 クライアントIDとシークレットを保存したJSONファイルのパス
CREDENTIALS_FILE = ""
TOKEN_FILE = "token.pickle"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# スプレッドシートIDと書き込む範囲
SPREADSHEET_ID = ""
RANGE_NAME = "シート1!A:E"


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


def get_gmail_service():
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    return service


def get_sheets_service():
    creds = authenticate()
    service = build("sheets", "v4", credentials=creds)
    return service


def list_messages(sender_email, subject_keyword):
    # 現在の時間を取得し、1時間前の時間を計算
    # now = datetime.datetime.now(datetime.timezone.utc)
    # one_hour_ago = int((now - datetime.timedelta(hours=2)).timestamp())

    # 3日前の0時の時間を取得
    now = datetime.datetime.now(datetime.timezone.utc)
    three_days_ago_midnight = datetime.datetime(
        now.year, now.month, now.day, 0, 0, 0, tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(days=3)
    three_days_ago_timestamp = int(three_days_ago_midnight.timestamp())

    # クエリを作成してメッセージを取得
    query = f"after:{three_days_ago_timestamp} from:{sender_email} subject:{subject_keyword}"
    print(query)
    # query = f"newer_than:2h from:{sender_email} subject:{subject_keyword}"

    service = get_gmail_service()
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    email_data_list = []

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        headers = msg["payload"]["headers"]

        email_data = {"id": message["id"]}
        for header in headers:
            if header["name"] == "From":
                email_data["From"] = header["value"]
            if header["name"] == "Subject":
                email_data["Subject"] = header["value"]
            if header["name"] == "To":
                email_data["To"] = header["value"]
            if header["name"] == "Date":
                email_data["Date"] = header["value"]

        email_data_list.append(email_data)

    print(email_data_list)
    return email_data_list


def write_to_sheets(email_data_list):
    service = get_sheets_service()

    try:
        sheet = service.spreadsheets()
        result = (
            sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        )
        existing_values = result.get("values", [])
        existing_ids = {row[0] for row in existing_values}

        new_values = []
        for email_data in email_data_list:
            if email_data["id"] not in existing_ids:
                new_values.append(
                    [
                        email_data.get("id", ""),
                        email_data.get("From", ""),
                        email_data.get("Subject", ""),
                        email_data.get("To", ""),
                        email_data.get("Date", ""),
                    ]
                )

        if new_values:
            body = {"values": new_values}
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

    except HttpError as err:
        print(err)


if __name__ == "__main__":
    sender_email = "no-reply@mercari.jp"  # 取得したいメールの送信元
    subject_keyword = "メルカリ"  # 取得したいメールの件名のキーワード
    email_data_list = list_messages(sender_email, subject_keyword)
    write_to_sheets(email_data_list)
