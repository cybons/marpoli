"""
このスクリプトは、稼働日に `scripts` フォルダ内のスクリプトを指定された頻度でスケジュールします。
稼働日は、日本の祝日と週末をチェックする WorkdayChecker クラスを使用して判定します。
エラーが発生した場合、Slackに通知します。
"""

import importlib.util
import os
import threading
import time
import traceback
from datetime import datetime, timedelta

import psutil
import schedule
import yaml
from workday_checker import WorkdayChecker

current_path = os.path.dirname(__file__)
# YAML設定ファイルの読み込み
with open(os.path.join(current_path, "config.yaml"), "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

script_folder = os.path.join(current_path, config["script_folder"])
script_frequencies = config["script_frequencies"]
start_hour = config["start_hour"]
end_hour = config["end_hour"]
# slack_webhook_url = config["slack_webhook_url"]
slack_channel = config.get("slack_channel", "#general")

# # SlackNotifierのインスタンス作成
# notifier = SlackHelper()

# PIDをファイルに保存
pid_file = "script_pid.txt"
pid = str(os.getpid())
with open(pid_file, "w") as f:
    f.write(pid)


def load_script(script_path):
    """
    指定されたパスのスクリプトをロードして実行します。

    Args:
        script_path (str): 実行するスクリプトのパス。
    """
    try:
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # module.main()
    except Exception:
        error_message = f"スクリプト {script_path} の実行中にエラーが発生しました:\n{traceback.format_exc()}"
        print(error_message)
        # notifier.send_message("channel", error_message)


def job(script_path):
    """
    スケジュールされたジョブを実行します。

    Args:
        script_path (str): 実行するスクリプトのパス。
    """
    print(f"ジョブが実行されました: {script_path} at {datetime.now()}")
    thread = threading.Thread(target=load_script, args=(script_path,))
    thread.start()


def handle_error_and_exit():
    """
    エラーが発生した場合に特別なクリーンアップを実行し、スクリプトを終了します。
    """
    error_message = (
        "終了前に特別なスクリプトを実行しています...\n" + traceback.format_exc()
    )
    print(error_message)
    # notifier.send_message(error_message, slack_channel)
    exit(1)


def schedule_tasks_for_date(date):
    """
    指定した日付のタスクをスケジュールします。

    Args:
        date (datetime.date): タスクをスケジュールする日付。
    """
    now = datetime.now()

    for script_name, frequency in script_frequencies.items():
        script_path = os.path.join(script_folder, script_name)
        start_time = datetime.combine(date, datetime.min.time()) + timedelta(
            hours=start_hour
        )
        end_time = datetime.combine(date, datetime.min.time()) + timedelta(
            hours=end_hour
        )

        print(f"スクリプト: {script_name}")
        initial_start_time = max(start_time, now)
        print(f"初回起動: {initial_start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"実行間隔: {frequency} 分")

        next_run_time = start_time
        first_scheduled_time = None

        while next_run_time < end_time:
            if next_run_time >= now:
                schedule.every().day.at(next_run_time.strftime("%H:%M")).do(
                    job, script_path=script_path
                )
                if first_scheduled_time is None:
                    first_scheduled_time = next_run_time
            next_run_time += timedelta(minutes=frequency)

        if first_scheduled_time:
            print(f"次回予定: {first_scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("次回予定: なし")

        last_scheduled_time = min(next_run_time, end_time)
        print(f"最終実行時間: {last_scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        print()

    print(f"{date} のタスクがスケジュールされました")


def run_scheduler():
    """
    スケジューラを実行して、保留中のジョブをチェックおよび実行します。
    また、毎日18:00に次の稼働日のタスクをスケジュールします。
    """
    today = datetime.now().date()
    checker = WorkdayChecker()
    # if checker.is_workday(today):
    schedule_tasks_for_date(today)

    while True:
        try:
            schedule.run_pending()
        except Exception:
            error_message = (
                "スケジューラがエラーに遭遇しました:\n" + traceback.format_exc()
            )
            print(error_message)
            # notifier.send_message(error_message, slack_channel)
            handle_error_and_exit()

        now = datetime.now()
        # 毎日18時に次の日のタスクをスケジュール
        if now.hour == 18 and now.minute == 0:
            checker = WorkdayChecker()
            next_working_day = checker.get_nearest_workday(
                now.date() + timedelta(days=1)
            )
            schedule_tasks_for_date(next_working_day)
        time.sleep(1)


def view_process(pid):
    process = psutil.Process(pid)
    print(f"PID: {process.pid}")
    print(f"Name: {process.name()}")
    print(f"Status: {process.status()}")
    print(f"CPU Usage: {process.cpu_percent(interval=1.0)}%")
    print(f"Memory Usage: {process.memory_info().rss / (1024 * 1024)} MB")
    print(f"Parent PID: {process.ppid()}")
    print(f"Execution Time: {process.create_time()}")


view_process(os.getpid())


def main():
    """
    スケジューラを初期化して開始するメイン関数。
    """
    try:
        run_scheduler()
    except Exception:
        error_message = (
            "メインループ外でスケジューラがエラーに遭遇しました:\n"
            + traceback.format_exc()
        )
        print(error_message)
        # notifier.send_message(SlackChannel.GENERAL, error_message)
        handle_error_and_exit()


if __name__ == "__main__":
    main()
