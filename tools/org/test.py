import pandas as pd
import networkx as nx
import numpy as np

# データの読み込み
org_df = pd.read_csv('org.csv', encoding='utf-8')  # エンコーディングは必要に応じて調整
user_df = pd.read_csv('ユーザー.csv', encoding='utf-8')

# 組織ツリーの構築
G = nx.DiGraph()
for _, row in org_df.iterrows():
    org_code = row['組織コード']
    parent_code = row['上位組織コード']
    G.add_node(org_code, name=row['組織名'], rank=row['ランク'], order=row['出力順'])
    if pd.notna(parent_code):
        G.add_edge(parent_code, org_code)

# 組織の親情報とランク情報を辞書化
parent_dict = org_df.set_index('組織コード')['上位組織コード'].to_dict()
rank_dict = org_df.set_index('組織コード')['ランク'].to_dict()

# ランク定義の確認（ユーザーの説明に基づく）
# 7: 係, 6: 課, 5: 部, 4: 事業部, 3: 本部, 2: (なし), 1: 会社
# 全員が課（ランク6）に属するように調整

# 役職コードの基準: 10 <= 役職コード <= 50 を責任者とみなす
def assign_org_code(row):
    pos_code = row['役職コード']
    if 10 <= pos_code <= 50:
        # 役職コードが10から50の範囲の場合、就労コードを組織コードとみなす
        return row['就労コード']
    else:
        # 一般社員は組織コードを使用
        return row['組織コード']

user_df['割り当て組織コード'] = user_df.apply(assign_org_code, axis=1)

# 割り当て組織のランクが7（係）の場合、親組織（ランク6: 課）に移動
def adjust_to_kaku(org_code):
    if pd.isna(org_code):
        return np.nan
    current_rank = rank_dict.get(org_code, np.nan)
    if current_rank == 7:
        parent_code = parent_dict.get(org_code, np.nan)
        if parent_code and rank_dict.get(parent_code, np.nan) == 6:
            return parent_code
    elif current_rank == 6:
        return org_code
    else:
        # ランク6に直接属していない場合
        return np.nan

user_df['最終組織コード'] = user_df['割り当て組織コード'].apply(adjust_to_kaku)

# 全員が課（ランク6）に属していることを確認
# ランク6に属さないユーザーをエラーとして抽出
unassigned_users = user_df[user_df['最終組織コード'].isna()]
if not unassigned_users.empty:
    print("エラー: ランク6の組織に割り当てられなかったユーザーが存在します。")
    print(unassigned_users)
    # エラー処理を続行する場合はコメントアウト
    # exit()

# ランク6に属したユーザーのみを対象
assigned_users = user_df.dropna(subset=['最終組織コード'])

# 組織ユーザー数の集計
# まず、各ユーザーが属する課ランク組織（ランク6）のみをカウント
user_counts = assigned_users.groupby('最終組織コード').size().reset_index(name='ユーザー数')

# 上位組織への合算
# ランク6（課）より上位の組織にユーザー数を加算
# ここでは、ランク6より上位の組織はランク5,4,3,2,1と仮定

# 組織コードからランク6の組織へのパスを取得
def get_all_ancestors(org_code):
    ancestors = list(nx.ancestors(G, org_code))
    return ancestors

# 組織ごとのユーザー数を格納する辞書
user_counts_dict = user_counts.set_index('最終組織コード')['ユーザー数'].to_dict()

# 上位組織にユーザー数を合算
for org_code, count in user_counts_dict.copy().items():
    ancestors = get_all_ancestors(org_code)
    for ancestor in ancestors:
        ancestor_rank = rank_dict.get(ancestor, np.nan)
        if ancestor_rank < 6:
            user_counts_dict[ancestor] = user_counts_dict.get(ancestor, 0) + count

# 最終的なユーザー数データフレーム
final_user_counts = pd.DataFrame(list(user_counts_dict.items()), columns=['組織コード', 'ユーザー数'])

# ランク情報を追加
final_user_counts['ランク'] = final_user_counts['組織コード'].map(rank_dict)

# ランク2から6のデータを抽出
final_user_counts = final_user_counts[final_user_counts['ランク'].isin([6,5,4,3,7])]

# ランク順にソート
final_user_counts = final_user_counts.sort_values(by=['ランク', '組織コード'], ascending=[True, True])

# ランク別に組織コードと組織名を追加
final_user_counts['組織名'] = final_user_counts['組織コード'].map(org_df.set_index('組織コード')['組織名'])

# ピボットテーブルを作成し、ランク2から6までの列を横並びにする
# ただし、ランク2は存在しないため、ランク1から6までとします

# 必要なランクの確認
required_ranks = [1,2,3,4,5,6]
available_ranks = sorted(final_user_counts['ランク'].unique())

# ランク2は存在しないため、スキップ
# ランク1: 会社, 3: 本部, 4: 事業部, 5: 部, 6: 課, 7: 係

# ランクごとにフィルタリング
rank_dfs = {}
for rank in range(1,7):
    rank_df = final_user_counts[final_user_counts['ランク'] == rank][['組織コード', '組織名', 'ユーザー数']]
    rank_df = rank_df.rename(columns={
        '組織コード': f'ランク{rank}_組織コード',
        '組織名': f'ランク{rank}_組織名',
        'ユーザー数': f'ランク{rank}_人数'
    })
    rank_dfs[rank] = rank_df

# 組織ツリーを基に、階層ごとの組織をマージ
# ここでは、階層が深くなるほど上位組織が存在することを前提とします
# 例えば、会社（ランク1） -> 本部（ランク3） -> 事業部（ランク4） -> 部（ランク5） -> 課（ランク6）

# 最終的な出力形式を決定する
# ランク1からランク6までの組織を横並びに表示し、人数を表示する

# 一例として、ランク1の組織を基準に他のランクをマージ
# 実際の組織構造に応じて調整が必要です

# ここでは、単純に全てのランクを横に並べて表示します
# 欠損ランクがある場合は、NaNで埋めます

output_df = pd.DataFrame()

for rank in range(1,7):
    if rank in rank_dfs:
        if output_df.empty:
            output_df = rank_dfs[rank]
        else:
            output_df = output_df.merge(rank_dfs[rank], how='outer')
    else:
        # ランクが存在しない場合、空の列を追加
        output_df[f'ランク{rank}_組織コード'] = np.nan
        output_df[f'ランク{rank}_組織名'] = np.nan
        output_df[f'ランク{rank}_人数'] = np.nan

# 欠損ランクを補完（ランクが飛んでいる場合、左のランクのデータをコピー）
for rank in range(1,7):
    if rank not in available_ranks:
        # ランクが存在しない場合、左のランク（rank-1）のデータをコピー
        if rank > 1:
            output_df[f'ランク{rank}_組織コード'] = output_df[f'ランク{rank-1}_組織コード']
            output_df[f'ランク{rank}_組織名'] = output_df[f'ランク{rank-1}_組織名']
            output_df[f'ランク{rank}_人数'] = output_df[f'ランク{rank-1}_人数']
        else:
            # ランク1が存在しない場合はスキップ
            pass

# 必要に応じて、重複を削除
output_df = output_df.drop_duplicates()

# ユーザー一覧の出力
user_list = assigned_users[['社員番号', '社員名', '最終組織コード']]
user_list = user_list.rename(columns={'最終組織コード': '課ランク組織コード'})
user_list['課ランク組織名'] = user_list['課ランク組織コード'].map(org_df.set_index('組織コード')['組織名'])

# 割り出せなかったメンバーの出力
# 既に unassigned_users を取得していますが、再度確認
# エラーとして抽出済みの場合は、必要に応じて別ファイルに保存
# ここでは、エラーが存在する場合に保存します
if not unassigned_users.empty:
    unassigned_users_list = unassigned_users[['社員番号', '社員名', '組織コード', '就労コード']]
    unassigned_users_list.to_excel('割り出せなかったメンバー.xlsx', index=False)
    print("割り出せなかったメンバーを '割り出せなかったメンバー.xlsx' に保存しました。")
else:
    print("全員が課ランク組織に割り当てられました。")

# 結果の保存
final_user_counts.to_excel('組織ユーザー数.xlsx', index=False)
user_list.to_excel('ユーザー一覧.xlsx', index=False)
output_df.to_excel('ランク別組織ユーザー数.xlsx', index=False)

# 結果の表示（オプション）
print("組織ユーザー数:")
print(final_user_counts)

print("\nユーザー一覧:")
print(user_list)

if not unassigned_users.empty:
    print("\n割り出せなかったメンバー:")
    print(unassigned_users_list)