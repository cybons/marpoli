def register_handlers(app):
    @app.command("/request")
    def open_request_form(ack, body, client, respond):
        ack()
        respond({"text": "ファイルリストを取得しています。少々お待ちください..."})

        def fetch_files_and_open_form():
            file_list = get_file_list()

            file_options = [
                {
                    "text": {"type": "plain_text", "text": file},
                    "value": file
                } for file in file_list
            ]

            assignee_options = [
                {
                    "text": {"type": "plain_text", "text": assignee["name"]},
                    "value": assignee["id"],
                }
                for assignee in ASSIGNEE_LIST
            ]

            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "request_form",
                    "title": {"type": "plain_text", "text": "依頼フォーム"},
                    "submit": {"type": "plain_text", "text": "送信"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "files_block",
                            "element": {
                                "type": "checkboxes",
                                "options": file_options,
                                "action_id": "files_select"
                            },
                            "label": {"type": "plain_text", "text": "ファイル/フォルダ"},
                        },
                        {
                            "type": "input",
                            "block_id": "date_block",
                            "element": {
                                "type": "datepicker",
                                "action_id": "date_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "作業日を選択",
                                },
                            },
                            "label": {"type": "plain_text", "text": "作業日"},
                        },
                        {
                            "type": "input",
                            "block_id": "assignee_block",
                            "element": {
                                "type": "checkboxes",
                                "options": assignee_options,
                                "action_id": "assignee_select"
                            },
                            "label": {"type": "plain_text", "text": "担当者"},
                        },
                    ],
                },
            )

        threading.Thread(target=fetch_files_and_open_form).start()
        
        
@app.view("request_form")
def handle_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    files = values["files_block"]["files_select"]["selected_options"]
    date = values["date_block"]["date_select"]["selected_date"]
    assignees = values["assignee_block"]["assignee_select"]["selected_options"]
    requester = body["user"]["id"]

    assignee_ids = [assignee["value"] for assignee in assignees]
    files_text = ', '.join([file['text']['text'] for file in files])

    for assignee_id in assignee_ids:
        client.chat_postMessage(
            channel=assignee_id,
            text=f"<@{requester}>さんからファイル/フォルダの確認依頼があります。\n"
            f"ファイル/フォルダ: {files_text}\n"
            f"作業日: {date}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{requester}>さんからファイル/フォルダの確認依頼があります。\n"
                        f"*ファイル/フォルダ:* {files_text}\n"
                        f"*作業日:* {date}"
                    }
                },
                {
                    "type": "actions",
                    "block_id": "response_actions",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "approve_request",
                            "text": {"type": "plain_text", "text": "承認"},
                            "style": "primary",
                            "value": requester
                        },
                        {
                            "type": "button",
                            "action_id": "request_revision",
                            "text": {"type": "plain_text", "text": "修正依頼"},
                            "style": "danger",
                            "value": f"{requester}|{files_text}|{date}"
                        }
                    ]
                }
            ]
        )