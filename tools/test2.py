import pandas as pd

def map_hierarchy_with_rank_corrected(
    df: pd.DataFrame,
    code_col: str = '組織コード',
    name_col: str = '組織名',
    rank_col: str = '組織ランク',
    parent_col: str = '上位組織コード',
    max_rank: int = 6
) -> pd.DataFrame:
    """
    組織の階層構造をランクに基づいて「上位組織1」から「上位組織6」までの列にマッピングし、
    各上位組織のランクも取得します。
    """
    # 組織コードから組織名およびランクへのマッピングを作成
    code_to_name = df.set_index(code_col)[name_col].to_dict()
    code_to_rank = df.set_index(code_col)[rank_col].to_dict()
    code_to_parent = df.set_index(code_col)[parent_col].to_dict()
    
    # ランクごとの上位組織を取得する関数
    def get_ancestors_by_rank(code, max_rank):
        ancestors = {f'上位組織{rank}': '' for rank in range(1, max_rank+1)}
        rank_values = {f'上位組織ランク{rank}': '' for rank in range(1, max_rank+1)}
        
        current_code = code_to_parent.get(code)
        while current_code and current_code in code_to_parent:
            current_rank = code_to_rank.get(current_code, None)
            current_name = code_to_name.get(current_code, '')
            if current_rank and 1 <= current_rank <= max_rank:
                ancestors[f'上位組織{current_rank}'] = current_name
                rank_values[f'上位組織ランク{current_rank}'] = current_rank
            current_code = code_to_parent.get(current_code)
        
        return list(ancestors.values()) + list(rank_values.values())
    
    # 上位組織1-6および上位組織ランク1-6の列名を生成
    ancestor_columns = [f'上位組織{rank}' for rank in range(1, max_rank+1)]
    rank_columns = [f'上位組織ランク{rank}' for rank in range(1, max_rank+1)]
    all_columns = ancestor_columns + rank_columns
    
    # 各組織に対して上位組織とそのランクを取得
    ancestors_df = df[code_col].apply(lambda x: get_ancestors_by_rank(x, max_rank)).apply(pd.Series)
    ancestors_df.columns = all_columns
    
    # 元のデータフレームに上位組織の列を追加
    result_df = pd.concat([df, ancestors_df], axis=1)
    
    return result_df

def find_duplicate_organizations(
    df: pd.DataFrame,
    upper_cols: list = ['上位組織1', '上位組織2', '上位組織3', '上位組織4', '上位組織5', '上位組織6'],
    name_col: str = '組織名',
    path_separator: str = ' > '
) -> pd.DataFrame:
    """
    同じ組織名が異なる上位組織の下に存在する場合をリストアップします。
    """
    # パスの作成
    df['パス'] = df[upper_cols].astype(str).agg(path_separator.join, axis=1)
    
    # 組織名ごとのユニークなパスの数をカウント
    dup_names_series = df.groupby(name_col)['パス'].nunique()
    
    # 複数のユニークなパスを持つ組織名を抽出
    duplicate_names = dup_names_series[dup_names_series > 1].index
    
    # 重複する組織名のデータをフィルタリング
    dup_df = df[df[name_col].isin(duplicate_names)]
    
    # 各組織名に対してユニークなパスをリスト化
    result = dup_df.groupby(name_col)['パス'].unique().reset_index()
    
    # パスのリストを見やすい形式（リスト）に変換
    result['パス'] = result['パス'].apply(lambda paths: list(paths))
    
    return result

def assign_unique_identifiers_with_abbreviation_corrected(
    df: pd.DataFrame,
    duplicates_df: pd.DataFrame,
    df_abbrev: pd.DataFrame,
    abbrev_cols: list = ['組織名', '略称'],
    name_col: str = '組織名',
    identifier_suffix_format: str = '({abbrev})'
) -> (pd.DataFrame, list):
    """
    重複する組織名に略称を付与して一意に識別できるようにします。
    略称リストに存在しない組織名があった場合はアラートを出力します。
    
    Parameters:
    ----------
    df : pd.DataFrame
        マッピング済みの組織データフレーム。
    duplicates_df : pd.DataFrame
        重複する組織名とそのパスを含むデータフレーム。
    df_abbrev : pd.DataFrame
        ランク2組織名と略称のリストを含むDataFrame。
    abbrev_cols : list, optional
        略称リストの列名（組織名と略称）。デフォルトは ['組織名', '略称']。
    name_col : str, optional
        組織名を表す列名。デフォルトは '組織名'。
    identifier_suffix_format : str, optional
        識別子のフォーマット。デフォルトは '({abbrev})'。
    
    Returns:
    -------
    pd.DataFrame
        略称が付与された組織名を含むデータフレーム。
    list
        略称リストに存在しない組織名のリスト（アラート用）。
    """
    df = df.copy()
    
    # 略称辞書の作成
    abbrev_dict = df_abbrev.set_index(abbrev_cols[0])[abbrev_cols[1]].to_dict()
    
    # アラート用リスト
    missing_abbrevs = []
    
    # 重複組織名のリスト
    duplicate_names = duplicates_df[name_col].tolist()
    
    for org_name in duplicate_names:
        # 該当する組織のデータを取得
        orgs = df[df[name_col] == org_name]
        
        # 各組織について識別子を決定
        for idx, row in orgs.iterrows():
            # ランク2の組織名を取得
            rank2_org = row['上位組織2']  # 上位組織2にランク2の組織名が入っていると仮定
            
            # 略称を取得
            if rank2_org in abbrev_dict:
                abbrev = abbrev_dict[rank2_org]
                new_name = f"{org_name} {identifier_suffix_format.replace('{abbrev}', abbrev)}"
            else:
                # 略称が見つからない場合、アラートリストに追加
                missing_abbrevs.append(rank2_org)
                new_name = org_name  # 略称がない場合は変更しない
            
            # 重複しないように追加のチェック
            if new_name in df[name_col].values and new_name != org_name:
                # 既に存在する場合はカウンターを追加
                count = 1
                while f"{new_name}_{count}" in df[name_col].values:
                    count += 1
                new_name = f"{new_name}_{count}"
            
            # 更新
            df.at[idx, name_col] = new_name
    
    return df, list(set(missing_abbrevs))  # 重複を排除

def update_user_groups_corrected(
    df_users: pd.DataFrame,
    df_org: pd.DataFrame,
    org_code_col_user: str = '組織コード',
    org_code_col_org: str = '組織コード',
    org_name_col_org: str = '組織名'
) -> pd.DataFrame:
    """
    ユーザー情報DataFrameの組織コードに基づいて組織名を更新します。
    
    Parameters:
    ----------
    df_users : pd.DataFrame
        ユーザー情報を含むDataFrame。
    df_org : pd.DataFrame
        略称が付与された組織データフレーム。
    org_code_col_user : str, optional
        ユーザー情報DataFrameでの組織コード列名。デフォルトは '組織コード'。
    org_code_col_org : str, optional
        組織データフレームでの組織コード列名。デフォルトは '組織コード'。
    org_name_col_org : str, optional
        組織データフレームでの組織名列名。デフォルトは '組織名'。
    
    Returns:
    -------
    pd.DataFrame
        更新されたユーザー情報DataFrame。
    """
    df_users = df_users.copy()
    
    # 組織コードと組織名のマッピング辞書を作成
    code_to_name = df_org.set_index(org_code_col_org)[org_name_col_org].to_dict()
    
    # 組織コード列を組織名に置き換える
    df_users['組織名'] = df_users[org_code_col_user].map(code_to_name).fillna(df_users[org_code_col_user])
    
    return df_users

# 使用例
if __name__ == "__main__":
    # 組織データの読み込み
    csv_file_path = 'organizations.csv'  # 実際のパスに変更してください
    df_org = pd.read_csv(csv_file_path, encoding='utf-8-sig')
    
    # 略称リストの読み込み
    abbreviation_file_path = 'rank2_abbreviations.xlsx'  # 実際のパスに変更してください
    df_abbrev = pd.read_excel(abbreviation_file_path, encoding='utf-8-sig')
    
    print("略称リストの読み込み:")
    print(df_abbrev.head())
    
    # 階層マッピングの実行（修正後）
    mapped_df = map_hierarchy_with_rank_corrected(
        df_org,
        code_col='組織コード',
        name_col='組織名',
        rank_col='組織ランク',
        parent_col='上位組織コード',
        max_rank=6
    )
    
    print("\n階層マッピング後のデータフレーム:")
    print(mapped_df.head())
    
    # 重複組織のリストアップ
    duplicate_orgs = find_duplicate_organizations(mapped_df)
    
    print("\n重複する組織名とそれぞれのパス:")
    print(duplicate_orgs)
    
    # 重複組織名に略称を付与
    mapped_df_unique, missing_abbrevs = assign_unique_identifiers_with_abbreviation_corrected(
        df=mapped_df,
        duplicates_df=duplicate_orgs,
        df_abbrev=df_abbrev,
        abbrev_cols=['組織名', '略称'],
        name_col='組織名',
        identifier_suffix_format='({abbrev})'
    )
    
    print("\n識別子を付与後のデータフレーム:")
    print(mapped_df_unique)
    
    # アラートの出力
    if missing_abbrevs:
        print("\nアラート: 略称リストに存在しないランク2の組織名が検出されました。")
        print("対象組織名:", missing_abbrevs)
        # アラートをExcelファイルに保存する（オプション）
        df_alert = pd.DataFrame({'存在しないランク2組織名': missing_abbrevs})
        df_alert.to_excel('missing_abbreviations_alert.xlsx', index=False, encoding='utf-8-sig')
    else:
        print("\nすべてのランク2組織名に対して略称が存在します。")
    
    # ユーザー情報のサンプルデータに組織コードを追加
    data_users = {
        'ユーザーID': [1001, 1002, 1003, 1004],
        '組織コード': [2, 4, 7, 8],  # 各ユーザーの組織コード
        'ユーザーグループ1': ['本社', '本社', '支社', '支社'],
        'ユーザーグループ2': ['エンジニアリング事業本部', '人事部', '営業部', '人事部'],
        'ユーザーグループ3': ['営業課', '人事課', '', ''],
        'ユーザーグループ4': ['営業課', '人事課', '営業部 (営業支社)', '人事部 (人事支社)'],
        'ユーザーグループ5': ['', '', '', ''],
        'ユーザーグループ6': ['', '', '', '']
    }
    
    df_users = pd.DataFrame(data_users)
    
    print("\nユーザー情報DataFrame（組織コード含む）:")
    print(df_users)
    
    # ユーザーグループ列を組織コードに基づいて更新
    df_users_updated = update_user_groups_corrected(
        df_users,
        df_org=mapped_df_unique,
        org_code_col_user='組織コード',
        org_code_col_org='組織コード',
        org_name_col_org='組織名'
    )
    
    print("\n更新後のユーザー情報DataFrame:")
    print(df_users_updated)
    
    # 組織データとユーザー情報データをCSVに保存
    mapped_df_unique.to_csv('organizations_unique.csv', index=False, encoding='utf-8-sig')
    df_users_updated.to_csv('users_updated.csv', index=False, encoding='utf-8-sig')