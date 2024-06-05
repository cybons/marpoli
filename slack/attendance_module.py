from slack_bolt import App

def send_attendance_buttons(app: App, channel_id):
    app.client.chat_postMessage(
        channel=channel_id,
        text="勤怠を報告してください",
        attachments=[
            {
                "text": "出勤/退勤を選択してください",
                "fallback": "ボタンをサポートしていません",
                "callback_id": "attendance_report",
                "actions": [
                    {
                        "name": "attendance",
                        "text": "出勤",
                        "type": "button",
                        "value": "check_in"
                    },
                    {
                        "name": "attendance",
                        "text": "退勤",
                        "type": "button",
                        "value": "check_out"
                    }
                ]
            }
        ]
    )

def register_attendance_handlers(app: App):
    @app.action("attendance_report")
    def handle_attendance_report(ack, body, logger):
        ack()
        action = body["actions"][0]
        status = action["value"]
        channel_id = body["channel"]["id"]
        user = body["user"]["id"]

        if status == "check_in":
            app.client.chat_postMessage(channel=channel_id, text=f"<@{user}> さんが出勤しました。")
        elif status == "check_out":
            app.client.chat_postMessage(channel=channel_id, text=f"<@{user}> さんが退勤しました。")

    @app.event("message")
    def handle_message_events(event, say):
        if "report_attendance" in event["text"]:
            send_attendance_buttons(app, event["channel"])