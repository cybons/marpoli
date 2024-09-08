import copy
from collections import defaultdict

import pandas as pd


# 組織情報の読み込みとツリー構造の構築
def read_organization_csv(file_path):
    df = pd.read_csv(file_path)

    # 組織情報を辞書に変換
    organizations = {}
    children = defaultdict(list)

    for _, row in df.iterrows():
        org_code = int(row["org_code"])
        parent_org_code = row["parent_org_code"]
        parent_org_code = int(parent_org_code) if not pd.isna(parent_org_code) else None

        organizations[org_code] = {
            "org_code": org_code,
            "parent_org_code": parent_org_code,
            "org_name": row["org_name"],
            "rank": int(row["rank"]),
            "children": [],
        }

        if parent_org_code is not None:
            children[parent_org_code].append(org_code)

    # 隣接リストから入れ子の辞書を構築
    def build_tree(org_code):
        org = organizations[org_code]
        org["children"] = [build_tree(child_code) for child_code in children[org_code]]
        return org

    root_orgs = [
        build_tree(org_code)
        for org_code in organizations
        if organizations[org_code]["parent_org_code"] is None
    ]
    return organizations, root_orgs


# 共通の組織情報の検索処理を関数に切り出し
def get_org_info(organizations, code):
    if code < 6:
        # コードが6未満の場合はNoneを返す
        return None
    else:
        # ランクを確認して返す
        org_info = organizations.get(code)
        if org_info:
            if org_info["rank"] == 7:
                # ランク7の場合、上位のランク6の組織を返す
                parent_org_code = org_info["parent_org_code"]
                if parent_org_code:
                    parent_org_info = organizations.get(parent_org_code)
                    if parent_org_info and parent_org_info["rank"] == 6:
                        return parent_org_info
            else:
                return org_info
    return None


# 組織情報の検索と条件に基づく操作
def get_organization(organizations, user_org_code, user_employment_code):
    # ユーザーの組織コードをチェック
    org_result = get_org_info(organizations, user_org_code)
    if org_result:
        return org_result

    # 就労コードをチェック
    emp_result = get_org_info(organizations, user_employment_code)
    if emp_result:
        return emp_result

    return None


# DataFrameに適用するための関数
def map_user_to_org(row, organizations):
    user_org_code = int(row["org_code"])
    user_employment_code = int(row["employment_code"])

    # 組織情報を取得
    result = get_organization(organizations, user_org_code, user_employment_code)

    if result:
        return result["org_code"], result["org_name"]
    else:
        return None, None


# ユーザー情報の読み込みと処理し、結果をDataFrameにセットする
def process_users(file_path, organizations):
    user_df = pd.read_csv(file_path)

    # applyを使用して各行にmap_user_to_org関数を適用し、タプルの結果を展開して新しい列に追加
    user_df[["mapped_org_code", "mapped_org_name"]] = user_df.apply(
        map_user_to_org, organizations=organizations, axis=1, result_type="expand"
    )

    return user_df


# 特定の組織をツリーから削除（末端組織のみ削除）
def remove_organizations_from_tree(organizations, exclude_orgs):
    # ツリーのディープコピーを作成
    organizations_copy = copy.deepcopy(organizations)

    # 除外する組織を削除（末端組織のみ）
    for exclude_org_code in list(
        exclude_orgs
    ):  # リストに変換してイテレーション中の変更を許可
        if exclude_org_code in organizations_copy:
            # 末端組織かどうかを確認（子供がいない場合）
            if not organizations_copy[exclude_org_code]["children"]:
                # 親組織の子リストからも削除
                parent_org_code = organizations_copy[exclude_org_code][
                    "parent_org_code"
                ]
                if parent_org_code and parent_org_code in organizations_copy:
                    organizations_copy[parent_org_code]["children"].remove(
                        organizations_copy[exclude_org_code]
                    )
                # 対象組織を削除
                del organizations_copy[exclude_org_code]
            else:
                print(
                    f"警告: 組織 {exclude_org_code} は子組織を持つため除外できません。"
                )

    return organizations_copy


def count_users_per_organization(root_orgs, users_df):
    # Step 1: ユーザーの所属組織ごとに人数をカウント
    user_counts = users_df["org_code"].value_counts().to_dict()

    # Step 2: 再帰的に下位組織を含むユーザー数を計算
    def count_users(org):
        # 自組織に属するユーザー数を取得
        user_count = user_counts.get(org["org_code"], 0)

        # 子組織を再帰的に探索し、ユーザー数を足し合わせる
        for child_org in org["children"]:
            user_count += count_users(child_org)

        # 結果を組織情報に格納
        org["total_users"] = user_count
        return user_count

    # 各ルート組織に対してユーザー数を計算
    for root_org in root_orgs:
        count_users(root_org)

    return root_orgs


def create_org_df_with_custom_columns(organizations):
    data = []

    for _, org_info in organizations.items():
        current_org = org_info
        ranks = [None] * 7  # ランク1からランク7の組織名を保持するリスト

        # 上位組織を辿ってランクごとに組織名を収集
        while current_org["parent_org_code"] is not None:
            rank_index = (
                current_org["rank"] - 1
            )  # ランクは1～7なので、インデックスとしては-1
            ranks[rank_index] = current_org["org_name"]
            parent_org_code = current_org["parent_org_code"]
            current_org = organizations.get(parent_org_code, None)
            if not current_org:
                break

        # 'children' 以外のすべてのキーを含む辞書を作成
        row = {key: value for key, value in org_info.items() if key != "children"}

        # カスタム列名でランク情報を更新
        rank_columns = {
            "root_organization": ranks[0],  # ランク1
            "division": ranks[2],  # ランク3
            "department": ranks[3],  # ランク4
            "section": ranks[4],  # ランク5
            "subsection": ranks[5],  # ランク6
            "unit": ranks[6],  # ランク7
        }

        # カスタム列をrowに追加
        row.update(rank_columns)

        data.append(row)

    # データフレームの作成
    org_df = pd.DataFrame(data)
    return org_df


# filtered_df = df[df['タイプ'] != '派遣社員']
# ファイルパスの設定
org_file_path = "organization.csv"
user_file_path = "users.csv"

# 組織情報とユーザー情報の処理
organizations, root_orgs = read_organization_csv(org_file_path)
user_results_df = process_users(user_file_path, organizations)

# 結果の表示（デバッグ用）
print(user_results_df)

# 結果の保存
output_file_path = "output_users.xlsx"
user_results_df.to_excel(output_file_path, index=False)
print(f"Results saved to {output_file_path}")

# 組織データの読み込みとツリー構築
organizations, root_orgs = read_organization_csv("organization.csv")

# ユーザー情報の読み込み
users_df = pd.read_csv(
    "users.csv"
)  # users.csvには'user_id'と'org_code'の列があると仮定
# 下位組織を含むユーザー数を計算
root_orgs_with_user_counts = count_users_per_organization(root_orgs, users_df)

# 結果を表示（各組織のユーザー数）
for root_org in root_orgs_with_user_counts:
    print(root_org)
