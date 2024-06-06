from slack_bolt import App

# 投票結果を保存するための辞書
votes = {}
poll_message_ts = None

def send_poll(app: App, channel_id, question, options):
    global poll_message_ts
    actions = [{"name": "poll", "text": option, "type": "button", "value": option} for option in options]
    response = app.client.chat_postMessage(
        channel=channel_id,
        text=question,
        attachments=[
            {
                "text": "投票してください",
                "fallback": "ボタンをサポートしていません",
                "callback_id": "poll_vote",
                "actions": actions
            },
            {
                "text": "投票結果を見るには以下のボタンを押してください",
                "fallback": "ボタンをサポートしていません",
                "callback_id": "show_results",
                "actions": [
                    {
                        "name": "results",
                        "text": "結果を見る",
                        "type": "button",
                        "value": "show_results"
                    }
                ]
            }
        ]
    )
    poll_message_ts = response["ts"]

def show_results_modal(app: App, trigger_id):
    result_text = "投票結果:\n"
    for option, count in votes.items():
        result_text += f"{option}: {count}票\n"
    app.client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "results_modal",
            "title": {
                "type": "plain_text",
                "text": "投票結果"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": result_text
                    }
                }
            ]
        }
    )

def register_poll_handlers(app: App):
    @app.action("poll_vote")
    def handle_poll_vote(ack, body, logger):
        ack()
        action = body["actions"][0]
        option = action["value"]
        channel_id = body["channel"]["id"]

        # 投票結果を更新
        if option in votes:
            votes[option] += 1
        else:
            votes[option] = 1

    @app.action("show_results")
    def handle_show_results(ack, body, logger):
        ack()
        trigger_id = body["trigger_id"]
        show_results_modal(app, trigger_id)

    @app.event("message")
    def handle_message_events(event, say):
        if "start_poll" in event["text"]:
            send_poll(app, event["channel"], "あなたの好きなプログラミング言語は何ですか？", ["Python", "JavaScript", "Java", "C++"])