import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# SQLiteファイルのパス
DB_FILE = "data.db"

# Excelファイルのパス
USER_FILE = "users.xlsx"
TASK_FILE = "tasks.xlsx"
HOURS_FOLDER = "hours_records"


# SQLiteのテーブルを初期化する関数
def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ユーザーテーブルの作成
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            社員番号 TEXT,
            名前 TEXT,
            SlackID TEXT,
            メールアドレス TEXT
        )
    """)

    # タスクテーブルの作成
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            タスク TEXT
        )
    """)

    # 作業時間テーブルの作成
    c.execute("""
        CREATE TABLE IF NOT EXISTS hours (
            ユーザー TEXT,
            タスク TEXT,
            時間 INTEGER,
            日付 TEXT
        )
    """)

    conn.commit()
    conn.close()


# SQLiteからデータをロードする関数
def load_data_from_db(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# SQLiteにデータを保存する関数
def save_data_to_db(table, df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql(table, conn, if_exists="replace", index=False)
    conn.close()


# Excelファイルからデータをロードする関数（初期化用）
def load_data_from_excel(file_path):
    return pd.read_excel(file_path)


# Excelファイルにデータを保存する関数
def save_data_to_excel(file_path, df):
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)


# 初期化処理
initialize_database()

# サイドバーのメニュー
st.sidebar.title("メニュー")
menu = st.sidebar.radio("ページを選択", ["時間入力", "タスク", "ユーザー"])

if menu == "ユーザー":
    st.title("ユーザー情報入力")
    df_users = load_data_from_db("SELECT * FROM users")
    edited_df_users = st.data_editor(df_users, num_rows="dynamic")

    if st.button("ユーザー情報を保存"):
        save_data_to_db("users", edited_df_users)
        st.success("ユーザー情報が保存されました。")

elif menu == "タスク":
    st.title("タスク入力")
    df_tasks = load_data_from_db("SELECT * FROM tasks")
    edited_df_tasks = st.data_editor(df_tasks, num_rows="dynamic")

    if st.button("タスクを保存"):
        save_data_to_db("tasks", edited_df_tasks)
        st.success("タスクが保存されました。")

elif menu == "時間入力":
    st.title("時間入力")

    df_users = load_data_from_db("SELECT * FROM users")
    df_tasks = load_data_from_db("SELECT * FROM tasks")

    # ユーザー選択
    user = st.selectbox("ユーザーを選択", df_users["名前"])

    # タスクと時間の入力
    task_hours = {}
    for task in df_tasks["タスク"]:
        hours = st.number_input(
            f"{task}に使った時間 (時間)", min_value=0, max_value=24, step=1
        )
        task_hours[task] = hours

    # `session_state`の初期化
    if "confirmation_needed" not in st.session_state:
        st.session_state.confirmation_needed = False

    # 確認用のボタン
    if st.button("登録"):
        # 確認が必要な状態にセット
        st.session_state.confirmation_needed = True

    # 確認が必要な場合の表示
    if st.session_state.confirmation_needed:
        st.write("### 登録確認")
        st.write(f"ユーザー: {user}")
        for task, hours in task_hours.items():
            st.write(f"{task}: {hours}時間")

        # 「はい」「いいえ」ボタン
        if st.button("はい"):
            try:
                # データをSQLiteとExcelに保存
                df_hours = load_data_from_db("SELECT * FROM hours")
                current_date = datetime.now().strftime("%Y-%m-%d")
                for task, hours in task_hours.items():
                    new_row = pd.DataFrame(
                        {
                            "ユーザー": [user],
                            "タスク": [task],
                            "時間": [hours],
                            "日付": [current_date],
                        }
                    )
                    df_hours = pd.concat([df_hours, new_row], ignore_index=True)
                save_data_to_db("hours", df_hours)

                # 時間データを個別のExcelファイルに保存
                if not os.path.exists(HOURS_FOLDER):
                    os.makedirs(HOURS_FOLDER)
                excel_file = os.path.join(
                    HOURS_FOLDER, f"hours_{user}_{current_date}.xlsx"
                )
                save_data_to_excel(excel_file, df_hours)

                st.success("時間が保存されました。")
                # 確認状態をリセット
                st.session_state.confirmation_needed = False
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        elif st.button("いいえ"):
            # 確認状態をリセット
            st.session_state.confirmation_needed = False
            st.info("登録がキャンセルされました。")
