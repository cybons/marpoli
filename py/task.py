from datetime import datetime


class Task:
    """
    タスクを表すクラス。
    """

    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        start_time: str,
        end_time: str,
        title: str,
        assignee: str,
        all_day: bool = False,
    ):
        """
        Taskクラスのコンストラクタ。

        Parameters:
        - start_date (datetime): タスクの開始日。
        - end_date (datetime): タスクの終了日。
        - start_time (str): タスクの開始時間。
        - end_time (str): タスクの終了時間。
        - title (str): タスクのタイトル。
        - assignee (str): タスクの担当者。
        - all_day (bool): 終日タスクかどうかのフラグ。
        """
        self.start_date = start_date
        self.end_date = end_date
        self.start_time = start_time
        self.end_time = end_time
        self.title = title
        self.assignee = assignee
        self.all_day = all_day

    def __repr__(self) -> str:
        """
        Taskクラスの文字列表現を返す。

        Returns:
        - str: タスクの文字列表現。
        """
        return f"Task({self.title}, {self.start_date}, {self.end_date}, {self.start_time}, {self.end_time}, {self.assignee}, {self.all_day})"
