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
                            "value": f"{requester}|{files_text}|{date}|{','.join(assignee_ids)}"
                        },
                        {
                            "type": "button",
                            "action_id": "request_revision",
                            "text": {"type": "plain_text", "text": "修正依頼"},
                            "style": "danger",
                            "value": f"{requester}|{files_text}|{date}|{','.join(assignee_ids)}"
                        }
                    ]
                }
            ]
        )

@app.action("resubmit_request")
def handle_resubmit_request(ack, body, client):
    ack()
    files_text, date, assignee_ids_str = body["actions"][0]["value"].split('|')
    initial_assignee_ids = assignee_ids_str.split(',')
    trigger_id = body["trigger_id"]

    assignee_options = [
        {
            "text": {"type": "plain_text", "text": assignee["name"]},
            "value": assignee["id"],
        }
        for assignee in ASSIGNEE_LIST
    ]

    initial_assignees = [
        {
            "text": {"type": "plain_text", "text": assignee["name"]},
            "value": assignee["id"],
        }
        for assignee in ASSIGNEE_LIST if assignee["id"] in initial_assignee_ids
    ]

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "resubmit_form",
            "title": {"type": "plain_text", "text": "再申請フォーム"},
            "submit": {"type": "plain_text", "text": "送信"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*ファイル/フォルダ:* {files_text}\n*作業日:* {date}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "assignee_block",
                    "element": {
                        "type": "checkboxes",
                        "options": assignee_options,
                        "initial_options": initial_assignees,
                        "action_id": "assignee_select"
                    },
                    "label": {"type": "plain_text", "text": "担当者"},
                },
            ],
            "private_metadata": f"{files_text}|{date}|{','.join(initial_assignee_ids)}"
        }
    )

@app.view("resubmit_form")
def handle_resubmission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    assignees = values["assignee_block"]["assignee_select"]["selected_options"]
    requester = body["user"]["id"]
    files_text, date, _ = body["view"]["private_metadata"].split('|')

    assignee_ids = [assignee["value"] for assignee in assignees]

    for assignee_id in assignee_ids:
        client.chat_postMessage(
            channel=assignee_id,
            text=f"<@{requester}>さんからファイル/フォルダの再確認依頼があります。\n"
            f"ファイル/フォルダ: {files_text}\n"
            f"作業日: {date}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{requester}>さんからファイル/フォルダの再確認依頼があります。\n"
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
                            "value": f"{requester}|{files_text}|{date}|{','.join(assignee_ids)}"
                        },
                        {
                            "type": "button",
                            "action_id": "request_revision",
                            "text": {"type": "plain_text", "text": "修正依頼"},
                            "style": "danger",
                            "value": f"{requester}|{files_text}|{date}|{','.join(assignee_ids)}"
                        }
                    ]
                }
            ]
        )
@app.action("request_revision")
    def handle_revision_request(ack, body, client):
        ack()
        requester, files_text, date, assignee_ids = body["actions"][0]["value"].split('|')
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "revision_form",
                "title": {"type": "plain_text", "text": "修正依頼フォーム"},
                "submit": {"type": "plain_text", "text": "送信"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "revision_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "revision_input",
                            "multiline": True,
                        },
                        "label": {"type": "plain_text", "text": "修正箇所"},
                    }
                ],
                "private_metadata": f"{requester}|{files_text}|{date}|{assignee_ids}"
            },
        )