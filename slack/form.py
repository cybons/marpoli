import os
import threading

# 担当者の名前とIDのリスト
ASSIGNEE_LIST = [
    {"name": "担当者A", "id": "U12345678"},
    {"name": "担当者B", "id": "U23456789"},
    {"name": "担当者C", "id": "U34567890"},
]

# ファイルサーバーのディレクトリを指定
FILE_SERVER_PATH = "/path/to/file/server"


def get_file_list(directory=FILE_SERVER_PATH):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            file_list.append(os.path.join(root, name))
        for name in dirs:
            file_list.append(os.path.join(root, name))
    return file_list


def register_handlers(app):
    @app.command("/request")
    def open_request_form(ack, body, client, respond):
        ack()
        respond({"text": "ファイルリストを取得しています。少々お待ちください..."})

        def fetch_files_and_open_form():
            file_list = get_file_list()

            file_options = [
                {"text": {"type": "plain_text", "text": file}, "value": file}
                for file in file_list
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
                                "type": "multi_static_select",
                                "action_id": "files_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "ファイルまたはフォルダを選択",
                                },
                                "options": file_options,
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "ファイル/フォルダ",
                            },
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
                                "type": "multi_static_select",
                                "action_id": "assignee_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "担当者を選択",
                                },
                                "options": assignee_options,
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
        files_text = ", ".join([file["text"]["text"] for file in files])

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
                            f"*作業日:* {date}",
                        },
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
                                "value": requester,
                            },
                            {
                                "type": "button",
                                "action_id": "request_revision",
                                "text": {"type": "plain_text", "text": "修正依頼"},
                                "style": "danger",
                                "value": f"{requester}|{files_text}|{date}",
                            },
                        ],
                    },
                ],
            )

    @app.action("approve_request")
    def handle_approve(ack, body, client):
        ack()
        requester = body["actions"][0]["value"]
        client.chat_postMessage(channel=requester, text="依頼が承認されました。")

    @app.action("request_revision")
    def handle_revision_request(ack, body, client):
        ack()
        requester, files_text, date = body["actions"][0]["value"].split("|")
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "revision_form",
                "title": {"type": "plain_text", "text": "修正依頼フォーム"},
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
                "private_metadata": f"{requester}|{files_text}|{date}",
            },
        )

    @app.view("revision_form")
    def handle_revision(ack, body, client):
        ack()
        values = body["view"]["state"]["values"]
        revision = values["revision_block"]["revision_input"]["value"]
        requester, files_text, date = body["view"]["private_metadata"].split("|")

        client.chat_postMessage(
            channel=requester, text=f"修正依頼がありました。修正箇所: {revision}"
        )

        client.chat_postMessage(
            channel=requester,
            text="修正後、再申請を行ってください。",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"修正依頼がありました。\n*修正箇所:* {revision}\n修正後、再申請を行ってください。",
                    },
                },
                {
                    "type": "actions",
                    "block_id": "resubmit_actions",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "resubmit_request",
                            "text": {"type": "plain_text", "text": "再申請"},
                            "style": "primary",
                            "value": f"{files_text}|{date}",
                        }
                    ],
                },
            ],
        )

    @app.action("resubmit_request")
    def handle_resubmit_request(ack, body, client):
        ack()
        files_text, date = body["actions"][0]["value"].split("|")
        trigger_id = body["trigger_id"]

        assignee_options = [
            {
                "text": {"type": "plain_text", "text": assignee["name"]},
                "value": assignee["id"],
            }
            for assignee in ASSIGNEE_LIST
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
                            "text": f"*ファイル/フォルダ:* {files_text}\n*作業日:* {date}",
                        },
                    },
                    {
                        "type": "input",
                        "block_id": "assignee_block",
                        "element": {
                            "type": "multi_static_select",
                            "action_id": "assignee_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "担当者を選択",
                            },
                            "options": assignee_options,
                        },
                        "label": {"type": "plain_text", "text": "担当者"},
                    },
                ],
            },
        )

    @app.view("resubmit_form")
    def handle_resubmission(ack, body, client):
        ack()
        values = body["view"]["state"]["values"]
        assignees = values["assignee_block"]["assignee_select"]["selected_options"]
        requester = body["user"]["id"]
        files_text, date = body["view"]["private_metadata"].split("|")

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
                            f"*作業日:* {date}",
                        },
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
                                "value": requester,
                            },
                            {
                                "type": "button",
                                "action_id": "request_revision",
                                "text": {"type": "plain_text", "text": "修正依頼"},
                                "style": "danger",
                                "value": f"{requester}|{files_text}|{date}",
                            },
                        ],
                    },
                ],
            )


# def main():
#     handler = SocketModeHandler(app, "YOUR_APP_TOKEN")
#     handler.start()


# if __name__ == "__main__":
#     main()
