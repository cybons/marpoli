"""
WorkdayCheckerモジュール

このモジュールは、祝日と特別な出社日・休日を考慮して稼働日を判定し、指定した稼働日後または前の日付を計算するためのクラスを提供します。
"""

import datetime

import holidays
import pandas as pd


class WorkdayChecker:
    """
    WorkdayCheckerクラス

    このクラスは、特定の国の祝日、特別な出社日、特別な休日を考慮して稼働日を判定します。

    Attributes:
        holidays: 指定された国の祝日を管理するオブジェクト
        special_workdays: 特別な出社日を保持するリスト
        special_holidays: 特別な休日を保持するリスト
    """

    def __init__(
        self, country: str = "JP", special_days_file: str | None = None
    ) -> None:
        """
        コンストラクタ

        Args:
            country (str): 祝日を取得する国のコード (デフォルトは 'JP')
            special_days_file (Optional[str]): 特別な出社日と休日を管理するCSVファイルのパス (省略可能)
        """
        self.holidays = holidays.CountryHoliday(country)
        self.special_workdays: list[datetime.date] = []
        self.special_holidays: list[datetime.date] = []
        if special_days_file:
            self.__load_special_days(special_days_file)

    def __load_special_days(self, file_path: str) -> None:
        """
        特別な出社日と休日をCSVファイルから読み込む

        Args:
            file_path (str): CSVファイルのパス
        """
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
            if row["type"] == "workday":
                self.add_special_workday(date)
            elif row["type"] == "holiday":
                self.add_special_holiday(date)

    def is_workday(self, date: datetime.date) -> bool:
        """
        指定した日付が稼働日かどうかを判定する

        Args:
            date (datetime.date): 判定する日付

        Returns:
            bool: 稼働日の場合はTrue、そうでない場合はFalse
        """
        if date.weekday() >= 5 and date not in self.special_workdays:
            return False
        if date in self.holidays and date not in self.special_workdays:
            return False
        if date in self.special_holidays:
            return False
        return True

    def add_special_workday(self, date: datetime.date) -> None:
        """
        特別な出社日を追加する

        Args:
            date (datetime.date): 追加する日付
        """
        if date not in self.special_workdays:
            self.special_workdays.append(date)

    def add_special_holiday(self, date: datetime.date) -> None:
        """
        特別な休日を追加する

        Args:
            date (datetime.date): 追加する日付
        """
        if date not in self.special_holidays:
            self.special_holidays.append(date)

    def get_nth_workday_from(
        self, start_date: datetime.date, n_days: int
    ) -> datetime.date:
        """
        指定した日付からn稼働日後または前の日付を取得する

        Args:
            start_date (datetime.date): 基準となる日付
            n_days (int): 取得する稼働日数（正の値で将来の日付、負の値で過去の日付）

        Returns:
            datetime.date: n稼働日後または前の日付
        """
        current_date = start_date
        days_count = 0
        step = 1 if n_days > 0 else -1

        while days_count < abs(n_days):
            current_date += datetime.timedelta(days=step)
            if self.is_workday(current_date):
                days_count += 1
        return current_date

    def get_nearest_workday(
        self, date: datetime.date, direction: str = "both"
    ) -> datetime.date:
        """
        指定した日付が休日の場合、最も近い稼働日を取得する

        Args:
            date (datetime.date): 判定する日付
            direction (str): 検索方向 ('before' または 'after' または 'both')

        Returns:
            datetime.date: 最も近い稼働日
        """
        if self.is_workday(date):
            return date

        offset = 1
        while True:
            if direction in ("both", "after"):
                next_date = date + datetime.timedelta(days=offset)
                if self.is_workday(next_date):
                    return next_date

            if direction in ("both", "before"):
                prev_date = date - datetime.timedelta(days=offset)
                if self.is_workday(prev_date):
                    return prev_date

            offset += 1


# 使用例
# workday_checker = WorkdayChecker(special_days_file="special_days.csv")
workday_checker = WorkdayChecker()

# 特定の日が稼働日かどうかをチェック
date_to_check = datetime.date(2024, 6, 1)
print(f"{date_to_check} は稼働日ですか？ {workday_checker.is_workday(date_to_check)}")

# 2稼働日後の日付を取得
start_date = datetime.date(2024, 5, 29)
n_days = 3
print(
    f"{start_date} の {n_days} 稼働日後: {workday_checker.get_nth_workday_from(start_date, n_days)}"
)

# 3稼働日前の日付を取得
n_days = -3
print(
    f"{start_date} の {n_days} 稼働日前: {workday_checker.get_nth_workday_from(start_date, n_days)}"
)

# 休日なら最も近い稼働日を取得（両方向）
date_to_check = datetime.date(2024, 8, 14)
print(
    f"{date_to_check} の最も近い稼働日 (両方向): {workday_checker.get_nearest_workday(date_to_check)}"
)

# 休日なら最も近い稼働日を取得（後ろ方向）
print(
    f"{date_to_check} の最も近い稼働日 (後ろ方向): {workday_checker.get_nearest_workday(date_to_check, 'after')}"
)

# 休日なら最も近い稼働日を取得（前方向）
print(
    f"{date_to_check} の最も近い稼働日 (前方向): {workday_checker.get_nearest_workday(date_to_check, 'before')}"
)
