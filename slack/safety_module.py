from slack_bolt import App

def send_safety_check_buttons(app: App, channel_id):
    app.client.chat_postMessage(
        channel=channel_id,
        text="緊急連絡：無事を報告してください",
        attachments=[
            {
                "text": "無事ですか？",
                "fallback": "ボタンをサポートしていません",
                "callback_id": "safety_check",
                "actions": [
                    {
                        "name": "safety",
                        "text": "無事です",
                        "type": "button",
                        "value": "safe"
                    },
                    {
                        "name": "safety",
                        "text": "助けが必要です",
                        "type": "button",
                        "value": "help"
                    }
                ]
            }
        ]
    )

def register_safety_handlers(app: App):
    @app.action("safety_check")
    def handle_safety_check(ack, body, logger):
        ack()
        action = body["actions"][0]
        status = action["value"]
        channel_id = body["channel"]["id"]
        user = body["user"]["id"]

        if status == "safe":
            app.client.chat_postMessage(channel=channel_id, text=f"<@{user}> さんが無事を報告しました。")
        elif status == "help":
            app.client.chat_postMessage(channel=channel_id, text=f"<@{user}> さんが助けを求めています。")

    @app.event("message")
    def handle_message_events(event, say):
        if "check_safety" in event["text"]:
            send_safety_check_buttons(app, event["channel"])