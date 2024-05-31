import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# GoogleカレンダーAPIのサービスを作成する関数
def get_calendar_service():
    creds, _ = google.auth.load_credentials_from_file(
        "path/to/credentials.json", scopes=["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=creds)
    return service


# 予定をGoogleカレンダーに追加する関数
def add_event(service, calendar_id, event):
    try:
        event_result = (
            service.events().insert(calendarId=calendar_id, body=event).execute()
        )
        print(f"Event created: {event_result['htmlLink']}")
        return event_result["id"]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


# 予定をGoogleカレンダーから削除する関数
def delete_event(service, calendar_id, event_id):
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Event deleted: {event_id}")
    except HttpError as error:
        print(f"An error occurred: {error}")


# 予定を更新する関数
def update_event(service, calendar_id, event_id, event):
    try:
        updated_event = (
            service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )
        print(f"Event updated: {updated_event['htmlLink']}")
        return updated_event["id"]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


# 予定データを取得する（ここでは例として固定データを使用）
def get_upcoming_events():
    return [
        {
            "unique_key": "1",
            "summary": "Meeting with Bob",
            "start": "2024-06-01T10:00:00",
            "end": "2024-06-01T11:00:00",
        },
        {
            "unique_key": "2",
            "summary": "Project deadline",
            "start": "2024-06-02T12:00:00",
            "end": "2024-06-02T13:00:00",
        },
    ]


# メイン処理
def main():
    service = get_calendar_service()
    calendar_id = "primary"  # カレンダーID（'primary'はデフォルトカレンダー）

    # 既存のカレンダーイベントを取得してユニークキーのマッピングを作成
    existing_events = (
        service.events().list(calendarId=calendar_id).execute().get("items", [])
    )
    existing_event_keys = {
        event["description"]: event["id"]
        for event in existing_events
        if "description" in event
    }

    # APIから取得した翌日以降の予定
    upcoming_events = get_upcoming_events()

    for event in upcoming_events:
        unique_key = event["unique_key"]
        event_body = {
            "summary": event["summary"],
            "description": unique_key,
            "start": {
                "dateTime": event["start"],
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": event["end"],
                "timeZone": "Asia/Tokyo",
            },
        }

        if unique_key in existing_event_keys:
            # イベントが既に存在する場合、更新する
            update_event(
                service, calendar_id, existing_event_keys[unique_key], event_body
            )
            existing_event_keys.pop(unique_key)
        else:
            # 新しいイベントの場合、追加する
            add_event(service, calendar_id, event_body)

    # 既存のイベントでAPIの予定に含まれていないものを削除
    for unique_key, event_id in existing_event_keys.items():
        delete_event(service, calendar_id, event_id)


if __name__ == "__main__":
    main()
