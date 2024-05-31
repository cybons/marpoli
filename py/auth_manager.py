import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# 使用するGoogle APIのスコープを定義
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]


class GoogleAuthManager:
    """
    Google APIのOAuth2認証を管理するクラス。

    このクラスはOAuth2の認証情報の読み込み、リフレッシュ、および新規取得を処理し、
    毎回認証を行わずに済むようにローカルに保存します。
    """

    def __init__(self):
        """
        GoogleAuthManagerを初期化する。

        ローカルファイルから既存の認証情報を読み込むか、
        新しい認証情報を取得するためにOAuth2フローを開始します。
        """
        self.creds = None
        self.token_file = "token.pickle"

        self._load_credentials()
        if not self.creds or not self.creds.valid:
            self._refresh_or_request_credentials()

    def _load_credentials(self) -> None:
        """
        ローカルのトークンファイルから認証情報を読み込む。
        """
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                self.creds = pickle.load(token)

    def _refresh_or_request_credentials(self) -> None:
        """
        認証情報が有効期限切れの場合はリフレッシュし、
        存在しない場合は新しい認証情報を取得する。
        """
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            self.creds = flow.run_local_server(port=0)
        with open(self.token_file, "wb") as token:
            pickle.dump(self.creds, token)

    def get_service(self, api_name: str, api_version: str) -> Resource:
        """
        Google APIサービスをビルドして返す。

        Parameters:
        - api_name (str): 使用するGoogle APIの名前。
        - api_version (str): 使用するGoogle APIのバージョン。

        Returns:
        - Resource: ビルドされたGoogle APIサービス。
        """
        return build(api_name, api_version, credentials=self.creds)
