def register_handlers(app):
    @app.command("/request")
    def open_request_form(ack, body, client, respond):
        ack()
        respond({"text": "ファイルリストを取得しています。少々お待ちください..."})

        def fetch_files_and_open_form():
            file_list = get_file_list()

            file_options = [
                {
                    "type": "checkboxes",
                    "options": [
                        {"text": {"type": "plain_text", "text": file}, "value": file}
                        for file in file_list
                    ],
                    "action_id": "files_select"
                }
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
                            "element": file_options[0],  # チェックボックスリストとして設定
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