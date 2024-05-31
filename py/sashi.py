import pandas as pd

# サンプルデータの作成
data = {
    "Server": ["Server1", "Server2", "Server3"],
    "Patch Applied": ["2024-05-01", "2024-05-02", "2024-05-03"],
    "Status": ["Success", "Success", "Failed"],
}
df = pd.DataFrame(data)

# LaTeXテンプレートの読み込み
with open("src/nn/template.tex", "r") as file:
    template = file.read()

# データの挿入
table_data = ""
for _, row in df.iterrows():
    table_data += (
        f"{row['Server']} & {row['Patch Applied']} & {row['Status']} \\\\\n\\hline\n"
    )

# テンプレートにデータを差し込む
output = template.replace("<<TABLE_DATA>>", table_data)

# 新しいLaTeXファイルとして保存
with open("report.tex", "w") as file:
    file.write(output)

print("LaTeX file generated successfully.")
