from datetime import datetime, timedelta

from task import Task


class TaskManager:
    """
    タスクを管理するクラス。
    """

    def __init__(self):
        """
        TaskManagerのコンストラクタ。
        """
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """
        タスクを追加する。

        Parameters:
        - task (Task): 追加するタスク。
        """
        self.tasks.append(task)

    def get_today_tasks(self) -> list[Task]:
        """
        今日のタスクを取得する。

        Returns:
        - list[Task]: 今日のタスクのリスト。
        """
        today = datetime.now().date()
        return [task for task in self.tasks if task.start_date.date() == today]

    def get_tomorrow_tasks(self) -> list[Task]:
        """
        明日のタスクを取得する。

        Returns:
        - list[Task]: 明日のタスクのリスト。
        """
        tomorrow = datetime.now().date() + timedelta(days=1)
        return [task for task in self.tasks if task.start_date.date() == tomorrow]

    def get_all_tasks_sorted(self) -> list[Task]:
        """
        全てのタスクを作業日、作業時間の昇順で取得する。

        Returns:
        - list[Task]: ソートされたタスクのリスト。
        """
        return sorted(self.tasks, key=lambda task: (task.start_date, task.start_time))

    def __repr__(self) -> str:
        """
        TaskManagerの文字列表現を返す。

        Returns:
        - str: タスクマネージャの文字列表現。
        """
        return f"TaskManager({self.tasks})"
