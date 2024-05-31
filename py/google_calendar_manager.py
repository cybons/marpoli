from datetime import datetime, timedelta

from auth_manager import GoogleAuthManager
from task import Task


class GoogleCalendarManager:
    """
    Googleカレンダーを操作するクラス。
    """

    def __init__(self, auth_manager: GoogleAuthManager):
        """
        GoogleCalendarManagerのコンストラクタ。

        Parameters:
        - auth_manager (GoogleAuthManager): 認証マネージャ。
        """
        self.service = auth_manager.get_service("calendar", "v3")

    def get_events(self, start_date: datetime, end_date: datetime) -> list[dict]:
        """
        指定された期間のイベントを取得する。

        Parameters:
        - start_date (datetime): 取得開始日。
        - end_date (datetime): 取得終了日。

        Returns:
        - list[dict]: 取得したイベントのリスト。
        """
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=start_date.isoformat() + "T00:00:00Z",
                timeMax=end_date.isoformat() + "T23:59:59Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    def add_event(self, task: Task) -> None:
        """
        Googleカレンダーにイベントを追加する。

        Parameters:
        - task (Task): 追加するタスク。
        """
        events = self.get_events(task.start_date, task.end_date)
        for event in events:
            if event["summary"] == task.title:
                print(
                    f"Event with title '{task.title}' already exists on {task.start_date}. Skipping."
                )
                return

        if task.all_day:
            event = {
                "summary": task.title,
                "start": {"date": task.start_date.isoformat()},
                "end": {"date": (task.end_date + timedelta(days=1)).isoformat()},
            }
        else:
            event = {
                "summary": task.title,
                "start": {
                    "dateTime": f"{task.start_date.isoformat()}T{task.start_time}:00",
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": f"{task.end_date.isoformat()}T{task.end_time}:00",
                    "timeZone": "UTC",
                },
            }

        event = self.service.events().insert(calendarId="primary", body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
