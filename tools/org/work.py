import pandas as pd
import networkx as nx

# データの読み込み
org_df = pd.read_csv('org.csv', encoding='utf-8')
user_df = pd.read_csv('ユーザー.csv', encoding='utf-8')

# 組織ツリーの構築
G = nx.DiGraph()
for _, row in org_df.iterrows():
    org_code = row['組織コード']
    parent_code = row['上位組織コード']
    G.add_node(org_code, name=row['組織名'], rank=row['ランク'], order=row['出力順'])
    if pd.notna(parent_code):
        G.add_edge(parent_code, org_code)

# ツリーの整合性チェック
if not nx.is_directed_acyclic_graph(G):
    raise ValueError("エラー: 組織ツリーにサイクル（循環参照）が含まれています。データを確認してください。")

# 組織の属性を辞書化
parent_dict = org_df.set_index('組織コード')['上位組織コード'].to_dict()
rank_dict = org_df.set_index('組織コード')['ランク'].to_dict()

# ユーザーの組織コードの割り当て
def assign_org_code(row):
    pos_code = row['役職コード']
    if 10 <= pos_code <= 50:
        return row['就労コード']
    else:
        return row['組織コード']

user_df['割り当て組織コード'] = user_df.apply(assign_org_code, axis=1)

# 割り当て組織のランクが7（係）の場合、親組織（ランク6: 課）に移動
def adjust_to_kaku(org_code):
    if pd.isna(org_code):
        return None
    current_rank = rank_dict.get(org_code)
    if current_rank == 7:
        parent_code = parent_dict.get(org_code)
        if parent_code and rank_dict.get(parent_code) == 6:
            return parent_code
    elif current_rank == 6:
        return org_code
    return None

user_df['最終組織コード'] = user_df['割り当て組織コード'].apply(adjust_to_kaku)

# 全員が課（ランク6）に属していることを確認
unassigned_users = user_df[user_df['最終組織コード'].isna()]
if not unassigned_users.empty:
    print("エラー: ランク6の組織に割り当てられなかったユーザーが存在します。")
    print(unassigned_users)
    # 必要に応じてエラー処理を行う
    # exit()

# ランク6に属したユーザーのみを対象
assigned_users = user_df.dropna(subset=['最終組織コード'])

# 組織ユーザー数の集計
user_counts = assigned_users.groupby('最終組織コード').size().reset_index(name='ユーザー数')

# 上位組織への合算
for org_code, count in user_counts.itertuples(index=False):
    ancestors = nx.ancestors(G, org_code)
    for ancestor in ancestors:
        if ancestor in user_counts['最終組織コード'].values:
            user_counts.loc[user_counts['最終組織コード'] == ancestor, 'ユーザー数'] += count
        else:
            user_counts = user_counts.append({'最終組織コード': ancestor, 'ユーザー数': count}, ignore_index=True)

# 最終的なユーザー数データフレーム
final_user_counts = user_counts.rename(columns={'最終組織コード': '組織コード'})
final_user_counts['ランク'] = final_user_counts['組織コード'].map(rank_dict)
final_user_counts['組織名'] = final_user_counts['組織コード'].map(org_df.set_index('組織コード')['組織名'])

# ランク別にピボットテーブルを作成
pivot_df = final_user_counts.pivot_table(index='組織コード', columns='ランク', values='ユーザー数', fill_value=0).reset_index()

# ランク別の組織名を追加
for rank in [1, 3, 4, 5, 6, 7]:
    pivot_df[f'ランク{rank}_組織名'] = pivot_df['組織コード'].map(
        org_df[org_df['ランク'] == rank].set_index('組織コード')['組織名']
    )

# ランク別の列名を整理
pivot_df = pivot_df.rename(columns={
    1: 'ランク1_人数',
    3: 'ランク3_人数',
    4: 'ランク4_人数',
    5: 'ランク5_人数',
    6: 'ランク6_人数',
    7: 'ランク7_人数'
})

# 組織コードと組織名の列を前に移動
cols = ['組織コード', 
        'ランク1_人数', 'ランク1_組織名',
        'ランク3_人数', 'ランク3_組織名',
        'ランク4_人数', 'ランク4_組織名',
        'ランク5_人数', 'ランク5_組織名',
        'ランク6_人数', 'ランク6_組織名',
        'ランク7_人数', 'ランク7_組織名']
pivot_df = pivot_df.reindex(columns=cols, fill_value=np.nan)

# ランク欠損の補完
for rank in [3, 4, 5]:
    count_col = f'ランク{rank}_人数'
    name_col = f'ランク{rank}_組織名'
    lower_rank = rank - 1
    lower_count_col = f'ランク{lower_rank}_人数'
    lower_name_col = f'ランク{lower_rank}_組織名'
    
    # 欠損部分を一つ下位ランクのデータで埋める
    pivot_df[count_col].fillna(pivot_df[lower_count_col], inplace=True)
    pivot_df[name_col].fillna(pivot_df[lower_name_col], inplace=True)

# ランク7の補完（ランク6を基準に補完）
pivot_df['ランク7_人数'].fillna(pivot_df['ランク6_人数'], inplace=True)
pivot_df['ランク7_組織名'].fillna(pivot_df['ランク6_組織名'], inplace=True)

# ユーザー一覧の出力
user_list = assigned_users[['社員番号', '社員名', '最終組織コード']].copy()
user_list = user_list.rename(columns={'最終組織コード': '課ランク組織コード'})
user_list['課ランク組織名'] = user_list['課ランク組織コード'].map(org_df.set_index('組織コード')['組織名'])

# 割り出せなかったメンバーの出力
if not unassigned_users.empty:
    unassigned_users_list = unassigned_users[['社員番号', '社員名', '組織コード', '就労コード']].copy()
    unassigned_users_list.to_excel('割り出せなかったメンバー.xlsx', index=False)
    print("割り出せなかったメンバーを '割り出せなかったメンバー.xlsx' に保存しました。")
else:
    print("全員が課ランク組織に割り当てられました。")

# 結果の保存
final_user_counts.to_excel('組織ユーザー数.xlsx', index=False)
user_list.to_excel('ユーザー一覧.xlsx', index=False)
pivot_df.to_excel('ランク別組織ユーザー数.xlsx', index=False)

# 結果の表示（オプション）
print("組織ユーザー数:")
print(final_user_counts)

print("\nユーザー一覧:")
print(user_list)

if not unassigned_users.empty:
    print("\n割り出せなかったメンバー:")
    print(unassigned_users_list)