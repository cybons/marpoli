from datetime import datetime

import pandas as pd
import streamlit as st

from .xml_data import parse_xml

# 定数の定義
NUMBER_COLUMN = "Number"
KEY_COLUMN = "キー"
DATE_COLUMN = "削除日"
STATUS_COLUMN = "状態"
EXIST_FLAG_COLUMN = "存在フラグ"


def update_status(row, max_number_dict, exist_flag_column):
    """
    スプレッドシートの行をXMLデータと比較し、ステータスを更新する。

    Parameters:
    - row: DataFrameの行（Seriesオブジェクト）
    - max_number_dict:
    - exist_flag_column:
    """
    key = row[KEY_COLUMN]  # キーを取得
    number = row[NUMBER_COLUMN]  # Numberを取得
    today = datetime.today().date()  # 今日の日付

    # キーの最大のNumberでない場合、状態を「-」に設定
    if number != max_number_dict[key]:
        return "-"

    # 削除日の有無で最初に分岐
    if row[DATE_COLUMN]:
        # 削除日が指定されている場合
        delete_date = datetime.strptime(row[DATE_COLUMN], "%Y-%m-%d").date()

        if row[exist_flag_column]:  # 存在フラグがTrue（XMLに存在する）場合
            # 削除日が未来の日付であれば正常な状態 "〇"
            if delete_date > today:
                return "〇"
            # 削除日が今日または過去の日付であれば矛盾 "矛盾！"
            else:
                return "矛盾！"
        else:  # 存在フラグがFalse（XMLに存在しない）場合
            # 削除日が今日の日付であれば警告 "▲"
            if delete_date == today:
                return "▲"
            # 削除日が未来の日付であれば正常な状態 "〇"
            elif delete_date > today:
                return "〇"
            # 削除日が過去の日付であれば削除済み "×"
            else:
                return "×"
    else:
        # 削除日が指定されていない場合
        if row[exist_flag_column]:  # 存在フラグがTrue（XMLに存在する）場合
            return "〇"
        else:  # 存在フラグがFalse（XMLに存在しない）場合
            return "！！"


def extract_missing_users(sheet_df, xml_list):
    # XMLに存在するがスプレッドシートに存在しないキーをリストに追加
    processed_keys = set(sheet_df[KEY_COLUMN])
    missing_keys = list(set(xml_list) - processed_keys)

    return missing_keys  # 欠落キーを返す


def process_combined_status_global(sheet_df, exist_flag_columns):
    """
    複数拠点のデータを基に存在フラグと状態を統合し、エラーデータを抽出する。

    Parameters:
    - sheet_df: スプレッドシートのデータフレーム
    - exist_flag_columns: 存在フラグを持つカラム名のリスト
    - status_columns: 状態を持つカラム名のリスト

    Returns:
    - 統合されたDataFrame
    - ErrorDataのDataFrame
    """
    # 統合された存在フラグを計算
    sheet_df[EXIST_FLAG_COLUMN] = sheet_df[exist_flag_columns].any(axis=1)

    # 状態の更新：統合された存在フラグを使ってステータスを更新
    max_number_dict = sheet_df.groupby(KEY_COLUMN)[NUMBER_COLUMN].max().to_dict()
    sheet_df[STATUS_COLUMN] = sheet_df.apply(
        update_status,
        axis=1,
        max_number_dict=max_number_dict,
        exist_flag_column=EXIST_FLAG_COLUMN,
    )

    # ErrorDataの抽出
    error_data = sheet_df[
        sheet_df[exist_flag_columns].nunique(axis=1) > 1  # 存在フラグが異なる場合
    ]

    return sheet_df, error_data


# XMLに存在するがスプレッドシートに存在しないキーを赤字で表示
def display_missing_keys(missing_keys):
    if missing_keys:
        st.write(
            "以下のキーはXMLに存在しますが、スプレッドシートに存在しません:",
            unsafe_allow_html=True,
        )
        for key in missing_keys:
            st.markdown(
                f"<span style='color:red;'>{key}</span>", unsafe_allow_html=True
            )


def main():
    # XMLファイルのパースとユーザー・IPリストの取得
    users, ip_dict = parse_xml
    print(users)
    print(ip_dict)


# サンプルデータの作成
data = {
    "キー": ["A", "B", "C", "A", "D", "D", "E", "E"],  # 重複したキー 'A', 'D', 'E'
    "Number": [1, 2, 3, 4, 5, 6, 7, 8],  # Number列
    "削除日": ["2023-09-01", "2023-09-05", "", "", "2023-09-10", "", "2023-09-15", ""],
    "状態": ["", "", "", "", "", "", "", ""],  # 状態は初期値として空にする
    "存在フラグ": [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ],  # 初期値としてFalse
}

# DataFrameの作成
sheet_df = pd.DataFrame(data)

# XMLから取得したキーのセット（キーが存在する場合のリスト）
kyoto_xml_list = {"A", "C", "D", "E"}
tokyo_xml_list = {"A", "C", "D", "F"}

# 存在フラグの生成を関数外で行う
sheet_df["kyoto_exist_flg"] = sheet_df[KEY_COLUMN].isin(kyoto_xml_list)
sheet_df["tokyo_exist_flg"] = sheet_df[KEY_COLUMN].isin(tokyo_xml_list)

kyoto_user_missing_keys = extract_missing_users(sheet_df, kyoto_xml_list)
tokyo_user_missing_keys = extract_missing_users(sheet_df, tokyo_xml_list)

# 統合された存在フラグに基づいてエラーを抽出し、ステータスを更新
sheet_df, error_data = process_combined_status_global(
    sheet_df, ["kyoto_exist_flg", "tokyo_exist_flg"]
)

print(sheet_df)

print(kyoto_user_missing_keys)
print(tokyo_user_missing_keys)
