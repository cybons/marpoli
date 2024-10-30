import logging
import unicodedata

import networkx as nx
import pandas as pd

# ロギングの設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def normalize_org_name(name):
    """
    組織名を正規化（NFKC形式に変換し、小文字に統一）。
    """
    if pd.isna(name):
        return ""
    name = unicodedata.normalize("NFKC", name)
    name = name.lower()
    return name


def build_tree(df):
    """
    データフレームからNetworkXの有向グラフ（ツリー）を構築。
    """
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_node(row["org_code"], name=row["org_name"], rank=row["rank"])
        if pd.notna(row["parent_code"]):
            G.add_edge(row["parent_code"], row["org_code"])
    return G


def assign_rank_columns(df, G, rank_levels=7):
    """
    ツリー構造に基づき、ランクごとのコードと名前の列を割り当てる。
    """
    # ランクごとのコードと名前の列を初期化
    for i in range(1, rank_levels + 1):
        df[f"rank{i}_code"] = None
        df[f"rank{i}_name"] = None

    def get_parent(node):
        preds = list(G.predecessors(node))
        return preds[0] if preds else None

    def assign_ranks(row):
        current = row["org_code"]
        current_rank = row["rank"]
        rank_dict = {}

        while current and current_rank >= 1:
            rank_code_col = f"rank{current_rank}_code"
            rank_name_col = f"rank{current_rank}_name"
            rank_dict[rank_code_col] = current
            rank_dict[rank_name_col] = G.nodes[current]["name"]

            parent = get_parent(current)
            current = parent
            if current:
                current_rank = G.nodes[current]["rank"]
            else:
                current_rank = None
        return pd.Series(rank_dict)

    # 各行に対してランク列を埋める
    rank_data = df.apply(assign_ranks, axis=1)
    df.update(rank_data)
    return df


def find_duplicate_names(df, rank_levels=7):
    """
    ランク4-7の組織名を正規化し、重複する名前を特定する。
    """
    df["org_name_normalized"] = df["org_name"].apply(normalize_org_name)
    # ランク4-7を抽出
    df_target = df[df["rank"].between(4, 7)].copy()
    # 重複する組織名を確認
    duplicate_counts = df_target["org_name_normalized"].value_counts()
    duplicate_names = duplicate_counts[duplicate_counts > 1].index.tolist()
    df_duplicates = df_target[
        df_target["org_name_normalized"].isin(duplicate_names)
    ].copy()
    return df, df_duplicates, duplicate_names


def prepare_mapping_table(mapping_data):
    """
    マッピングデータを準備し、略称を()で囲む。
    ランク2またはランク3の組織のみを対象とする。
    """
    df_mapping = pd.DataFrame(mapping_data)

    # 略称を()で囲む
    def wrap_parentheses(abbr):
        return f"（{abbr}）" if pd.notna(abbr) and abbr.strip() != "" else ""

    df_mapping["abbreviation"] = df_mapping["abbreviation"].apply(wrap_parentheses)
    # ランク2またはランク3の組織のみを含める
    # ここでは、マッピングデータにランク情報がないため、外部でランク2または3の組織コードを指定する必要があります
    # 例として、ランク2とランク3の組織コードのみを含める
    # 実際のデータに合わせて調整してください
    df_mapping = df_mapping[
        df_mapping["org_code"].isin(["B", "C"])
    ]  # 例としてランク2と3のコードを指定
    mapping_dict = df_mapping.set_index("org_code")["abbreviation"].to_dict()
    return mapping_dict


def validate_mapping_data(df_duplicates, mapping_dict):
    """
    マッピングデータにランク2またはランク3の略称が存在するかを検証。
    存在しない場合、アラートを出力。
    """
    alerts = []
    for _, row in df_duplicates.iterrows():
        # ランク2とランク3のコードを取得
        rank2_code = row.get("rank2_code")
        rank3_code = row.get("rank3_code")
        # ランク2またはランク3の略称が存在するか確認
        if rank2_code and mapping_dict.get(rank2_code, ""):
            continue
        elif rank3_code and mapping_dict.get(rank3_code, ""):
            continue
        else:
            alert_msg = (
                f"組織名 '{row['org_name']}' (コード: {row['org_code']}) のランク2 ('{rank2_code}') "
                f"またはランク3 ('{rank3_code}') の略称がマッピングデータに存在しません。"
            )
            alerts.append(alert_msg)

    if alerts:
        for alert in alerts:
            logging.warning(alert)
    else:
        logging.info(
            "すべての重複する組織に対して適切な略称がマッピングデータに存在します。"
        )


def add_abbreviations_to_names(
    df, df_duplicates, mapping_dict, duplicate_names, rank_levels=7
):
    """
    重複する組織名に対して、上位組織の略称を基に識別子を付与する。
    """

    # 略称を取得する関数
    def get_abbreviation(row):
        rank2_code = row["rank2_code"]
        rank3_code = row["rank3_code"]
        abbr = ""
        if rank2_code and mapping_dict.get(rank2_code, ""):
            abbr = mapping_dict[rank2_code]
        elif rank3_code and mapping_dict.get(rank3_code, ""):
            abbr = mapping_dict[rank3_code]
        return abbr

    # 略称を取得して新しい列に格納
    df_duplicates["abbreviation"] = df_duplicates.apply(get_abbreviation, axis=1)

    # 識別子を組織名に追加する関数
    def append_abbr(row):
        return (
            f"{row['org_name']} {row['abbreviation']}"
            if row["abbreviation"]
            else row["org_name"]
        )

    # 識別子を追加
    df_duplicates["org_name_unique"] = df_duplicates.apply(append_abbr, axis=1)

    # ランク4-7の組織名を更新
    for _, row in df_duplicates.iterrows():
        org_code = row["org_code"]
        org_rank = row["rank"]
        updated_name = row["org_name_unique"]
        rank_name_col = f"rank{org_rank}_name"
        df.loc[df["org_code"] == org_code, rank_name_col] = updated_name

    # 補助列を削除
    df.drop(
        ["org_name_normalized", "abbreviation", "org_name_unique"],
        axis=1,
        inplace=True,
        errors="ignore",
    )

    return df


def main():
    """
    メイン関数：組織データを処理し、識別子を付与したrank1〜rank7の組織名を出力する。
    """
    # サンプルデータ
    data = {
        "org_code": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
        "parent_code": [None, "A", "A", "B", "B", "C", "C", "D", "E", "H", "I", "J"],
        "org_name": [
            "Root",
            "Dept1",
            "Dept2",
            "Team",
            "Team",
            "Team",
            "Team",
            "Team",
            "Team",
            "Team",
            "Team",
            "Team",
        ],
        "rank": [1, 2, 2, 4, 4, 4, 4, 5, 5, 6, 6, 7],
    }

    df = pd.DataFrame(data)

    # ツリー構築
    G = build_tree(df)

    # ランクごとのコードと名前の列を割り当て
    df = assign_rank_columns(df, G, rank_levels=7)

    # 重複する組織名を特定
    df, df_duplicates, duplicate_names = find_duplicate_names(df, rank_levels=7)

    if not df_duplicates.empty:
        # マッピングデータの準備
        mapping_data = {
            "org_code": ["B", "C"],
            "org_name": ["Dept1", "Dept2"],
            "abbreviation": ["D1", "D2"],  # 括弧なし
        }

        mapping_dict = prepare_mapping_table(mapping_data)

        # マッピングデータの検証
        validate_mapping_data(df_duplicates, mapping_dict)

        # 識別子を組織名に付与
        df = add_abbreviations_to_names(
            df, df_duplicates, mapping_dict, duplicate_names, rank_levels=7
        )
    else:
        logging.info("ランク4-7に重複する組織名は存在しません。")

    # 最終的なデータフレームの表示
    print("\n最終的なデータフレーム（識別子付き）:")
    print(df)


if __name__ == "__main__":
    main()
