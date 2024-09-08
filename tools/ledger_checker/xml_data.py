import os

from lxml import etree


def check_file_conditions(selected_files: list):
    # 各条件の初期状態を設定
    conditions = {
        "tokyo": None,
        "kyoto": None,
        "kikan": None,
        "gcp_kikan": None,
        "gcp_dmz": None,
    }

    # 条件に一致するファイルを確認
    for file in selected_files:
        filename = os.path.basename(file.name).lower()

        if ("東京" in filename or "tokyo" in filename) and "infw" in filename:
            conditions["tokyo"] = file

        if ("京都" in filename or "kyoto" in filename) and "infw" in filename:
            conditions["kyoto"] = file

        # "kikan"のみを含む場合（"gcp-kikan"のような組み合わせは除く）
        if "kikan" in filename and "gcp" not in filename:
            conditions["kikan"] = file

        if "gcp" in filename and "kikan" in filename:
            conditions["gcp_kikan"] = file

        if "gcp" in filename and "dmz" in filename:
            conditions["gcp_dmz"] = file

    # 全ての条件が満たされているかどうかを確認
    state = all(conditions.values())

    return state, conditions


def parse_xml():
    # サンプルのXMLデータ
    xml_data = """
    <root>
        <device>
            <options>
                <groups>
                    <rules>
                        <users>
                            <member> user1 </member>
                            <member>user2</member>
                        </users>
                        <ip>
                            <member type="ip">192.168.1.1</member>
                            <member type="fqdn">example.com</member>
                        </ip>
                    </rules>
                    <rules>
                        <users>
                            <member>user2</member>
                            <member> user3 </member>
                        </users>
                        <ip>
                            <member type="ip">192.168.1.1</member>  <!-- 重複するIP -->
                            <member type="fqdn">example2.com</member>
                        </ip>
                    </rules>
                </groups>
            </options>
        </device>
    </root>
    """

    # XMLをパースしてElementTreeオブジェクトに変換
    root = etree.fromstring(xml_data)

    # XPathを使ってすべてのユーザーを取得
    user_elements = root.xpath("//rules/users/member")
    users = {user.text.strip() for user in user_elements}

    # XPathを使ってすべてのIPを取得して辞書に変換
    ip_elements = root.xpath("//rules/ip/member")
    ip_dict = {ip.get("type"): ip.text for ip in ip_elements}

    print("ユーザー一覧:", users)
    print("IP一覧:", ip_dict)
    return users, ip_dict


parse_xml()
