import logging
import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

current_folder = os.path.dirname(__file__)

# ログ取るよ
logging.basicConfig(filename="app.log", level=logging.INFO)

# SQLiteファイルのパス
DB_FILE = "data.db"

# Excelファイルのパス
HOURS_FOLDER = "hours_records"


# SQLiteのテーブルを初期化する関数
def initialize_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Users Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                employee_code TEXT PRIMARY KEY,
                employee_name TEXT NOT NULL,
                slack_id TEXT UNIQUE,
                email TEXT UNIQUE
            )
        """)

        # Tasks Table with Auto-increment ID
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                task_name TEXT UNIQUE NOT NULL
            )
        """)

        # Hours Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                work_time REAL,
                work_date TEXT,
                FOREIGN KEY (employee_code) REFERENCES users(employee_code),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        conn.close()


# SQLiteからデータをロードする関数（キャッシュ使うよ）
# @st.cache_data
def load_data_from_db(query):
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(query, conn)
        logging.info(f"Data loaded with query: {query}")
        return df
    except sqlite3.Error as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        logging.error(f"Error loading data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# データベースにデータを挿入する関数
def insert_into_db(table, data):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if table == "hours":
            c.execute(
                """
                INSERT INTO hours (employee_code, task_id, work_time, work_date) 
                VALUES (?, ?, ?, ?)
            """,
                (
                    data["employee_code"],
                    data["task_id"],
                    data["work_time"],
                    data["work_date"],
                ),
            )

        conn.commit()
        logging.info(f"Inserted data into {table}: {data}")
    except sqlite3.IntegrityError as e:
        st.error(f"データの重複または不整合: {e}")
        logging.error(f"Integrity error: {e}")
    except sqlite3.Error as e:
        st.error(f"データベースエラー: {e}")
        logging.error(f"Database error: {e}")
    finally:
        conn.close()


# Excelファイルにデータを保存する関数
def save_data_to_excel(file_path, df):
    try:
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        logging.info(f"Data saved to Excel: {file_path}")
    except Exception as e:
        st.error(f"Excelファイルの保存に失敗しました: {e}")
        logging.error(f"Error saving Excel: {e}")


# SQLiteにデータを保存する関数
def save_data_to_db(table, df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql(table, conn, if_exists="replace", index=False)
    conn.close()


# Excelファイルからデータをロードする関数（初期化用）
def load_data_from_excel(file_path):
    return pd.read_excel(file_path)


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

    df_users = load_data_from_db(
        "SELECT employee_code, employee_name, slack_id FROM users"
    )
    df_tasks = load_data_from_db("SELECT * FROM tasks")

    if df_users.empty:
        st.error("ユーザーデータが存在しません。ユーザー情報を入力してください。")
    elif df_tasks.empty:
        st.error("タスクデータが存在しません。タスク情報を入力してください。")
    else:
        # ユーザー選択
        user = st.selectbox("ユーザーを選択", df_users["employee_name"])
        selected_user = df_users[df_users["employee_name"] == user].iloc[0]
        employee_code = selected_user["employee_code"]
        slack_id = selected_user["slack_id"]

        # タスクと時間の入力
        task_hours = {}
        for _, task in df_tasks.iterrows():
            hours = st.number_input(
                f"{task["task_name"]}に使った時間 (時間)",
                min_value=0.0,
                max_value=24.0,
                step=0.25,
                format="%.2f",
            )
            logging.debug(task)
            if hours > 0:
                task_hours[task["id"]] = hours

        # `session_state`の初期化
        if "confirmation_needed" not in st.session_state:
            st.session_state.confirmation_needed = False

        # 確認用のボタン
        if st.button("登録"):
            # 確認が必要な状態にセット
            if not task_hours:
                st.error("少なくとも1つのタスクに時間を入力してください。")
            else:
                st.session_state.confirmation_needed = True

        # 確認が必要な場合の表示
        if st.session_state.confirmation_needed:
            st.write(f"社員番号: {employee_code}")
            st.write(f"名前: {user}")
            # st.write(f"Slack ID: {slack_id}")
            st.write("#### タスクと時間")
            for task_id, hours in task_hours.items():
                task_name = df_tasks[df_tasks["id"] == task_id]["task_name"].values[0]
                st.write(f"{task_name}: {hours}時間")

            # 「はい」「いいえ」ボタンを横並びに配置
            col1, col2 = st.columns(2)
            with col1:
                if st.button("はい"):
                    try:
                        current_date = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                        records_to_insert = []
                        records_for_excel = []
                        for task_id, hours in task_hours.items():
                            record = {
                                "employee_code": employee_code,
                                "task_id": task_id,
                                "work_time": hours,
                                "work_date": current_date,
                            }
                            records_to_insert.append(record)

                            # Excel用データに必要な情報を追加
                            task_name = df_tasks[df_tasks["id"] == task_id][
                                "task_name"
                            ].values[0]
                            records_for_excel.append(
                                {
                                    "employee_code": employee_code,
                                    "employee_name": user,
                                    "slack_id": slack_id,
                                    "task_name": task_name,
                                    "work_time": hours,
                                    "work_date": current_date,
                                }
                            )

                        # データベースに挿入
                        for record in records_to_insert:
                            insert_into_db("hours", record)

                        # Excelに保存
                        if not os.path.exists(HOURS_FOLDER):
                            os.makedirs(HOURS_FOLDER)
                        excel_file = os.path.join(
                            HOURS_FOLDER, f"hours_{employee_code}_{current_date}.xlsx"
                        )
                        df_excel = pd.DataFrame(records_for_excel)
                        save_data_to_excel(excel_file, df_excel)

                        st.success("時間が保存されました。")
                        # 確認状態をリセット
                        st.session_state.confirmation_needed = False
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
            with col2:
                if st.button("いいえ"):
                    # 確認状態をリセット
                    st.session_state.confirmation_needed = False
                    st.info("登録がキャンセルされました。")
