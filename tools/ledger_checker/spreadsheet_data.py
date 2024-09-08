"""
spreadsheet_data モジュール

このモジュールはGoogleスプレッドシートからデータを取得し、指定された条件に基づいて
pandas DataFrameとして返す関数を提供します。データの取得には gspread ライブラリを使用し、
認証には OAuth2 認証情報を必要とします。

主要関数:
- load_sheets_config: 指定されたシートコンフィグファイルを読み込み、dictを内包したリストを返す
- get_sheet_data: 指定されたスプレッドシートのシートからデータを取得し、DataFrameを返す
- get_all_sheets_data: 複数のスプレッドシートの設定に基づき、すべてのシートのデータをまとめて返す
"""

import json
import os
import pickle
from datetime import datetime

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# Google Sheets APIの認証情報を設定
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_client():
    credentials = Credentials.from_service_account_file(
        "path/to/credentials.json", scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    return client


# JSONファイルから設定を読み込む関数
def load_sheets_config(json_file_path: str) -> list[dict]:
    """
    JSONファイルからスプレッドシートの設定を読み込む。

    Parameters:
    - json_file_path (str): JSONファイルのパス

    Returns:
    - list[dict]: スプレッドシート設定のリスト
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            sheets_config = json.load(file)

    except FileNotFoundError as e:
        raise FileNotFoundError(f"ファイル {json_file_path} が見つかりません。") from e

    except json.JSONDecodeError as e:
        raise ValueError(f"JSONファイルの読み込み中にエラーが発生しました: {e}") from e

    return sheets_config


def fetch_sheets_data(
    sheet_config: dict, use_cache: bool = True, cache_dir: str = "cache"
) -> pd.DataFrame:
    """
    指定したシートのデータを取得し、指定されたヘッダーでDataFrameを作成する。
    またキャッシュを利用して効率的に取得する（24時間保持する）。

    Parameters:
    - sheet_config (dict): シートの設定を含む辞書
    - use_cache (bool): キャッシュを使用するかどうか
    - cache_dir (str): キャッシュを保存するディレクトリ

    Returns:
    - pd.DataFrame: 取得したデータを格納したDataFrame
    """
    # キャッシュディレクトリを作成（存在しない場合）
    try:
        os.makedirs(cache_dir, exist_ok=True)

    except OSError as e:
        raise OSError(
            f"キャッシュディレクトリ {cache_dir} を作成できませんでした: {e}"
        ) from e

    # キャッシュファイル名を生成
    cache_file = os.path.join(cache_dir, f"{sheet_config['display_name']}.pkl")

    # キャッシュが存在し、キャッシュを使用する場合
    if use_cache and os.path.exists(cache_file):
        # キャッシュファイルの作成日を確認し、日付が変わっていなければキャッシュを使用
        cache_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_modified_time.date() == datetime.now().date():
            with open(cache_file, "rb") as f:
                return pickle.load(f)

    # スプレッドシートを開く
    try:
        client = get_client()
        sheet = client.open_by_key(sheet_config["spreadsheet_id"])
        worksheet = sheet.worksheet(sheet_config["sheet_name"])

        # 列の範囲を取得してデータを抽出
        data = worksheet.get(
            f'{sheet_config["columns_range"][0]}{sheet_config["start_row"]}:{sheet_config["columns_range"][1]}',
            value_render_option="FORMATTED_VALUE",
        )

        # データフレームに変換し、ヘッダーを設定
        df = pd.DataFrame(data, columns=sheet_config["headers"])

        # データフレームをキャッシュとして保存
        with open(cache_file, "wb") as f:
            pickle.dump(df, f)

        return df

    except gspread.exceptions.APIError as e:
        raise ConnectionError(
            f"スプレッドシートAPIの呼び出し中にエラーが発生しました: {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"スプレッドシートからデータを取得中にエラーが発生しました: {e}"
        ) from e


def get_all_sheets_data(sheets_config: list[dict]) -> dict[str, pd.DataFrame]:
    """
    複数のスプレッドシート設定からデータを取得し、すべてのDataFrameを辞書としてまとめる。

    Parameters:
    - sheets_config (list[dict]): 各シートの設定を含む辞書のリスト

    Returns:
    - dict[str, pd.DataFrame]: 表記名と取得したデータを格納したDataFrameの辞書
    """
    all_data = {}
    for config in sheets_config:
        df = fetch_sheets_data(config)
        all_data[config["display_name"]] = df

    return all_data


def rewrite_sheets_data():
    # Google Sheets APIの認証情報を設定
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        "path/to/credentials.json", scopes=SCOPES
    )
    client = gspread.authorize(credentials)

    # スプレッドシートを開く
    spreadsheet_id = "your_spreadsheet_id"
    sheet_name = "Sheet1"
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # データフレームの例
    data = {"A列": [1, 2, 3, 4, 5], "B列": ["a", "b", "c", "d", "e"]}
    df = pd.DataFrame(data)

    # 特定の列（例：B列）をリストに変換
    column_data = df["B列"].tolist()

    # データを書き込む範囲を指定（例：B2:B6に書き込む）
    cell_range = f"B2:B{len(column_data) + 1}"

    # リスト形式のデータをスプレッドシートの範囲に書き込む
    sheet.update(cell_range, [[value] for value in column_data])

    print("データの書き込みが完了しました。")
