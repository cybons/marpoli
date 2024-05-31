import pandas as pd
import pyodbc
from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph


def connect_to_access(db_path):
    """Accessデータベースに接続する"""
    conn_str = r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};" f"DBQ={db_path};"
    connection = pyodbc.connect(conn_str)
    return connection


def get_access_tables_and_columns(connection):
    """Accessデータベースのテーブルとフィールド情報を取得する"""
    cursor = connection.cursor()
    tables = []
    for row in cursor.tables(tableType="TABLE"):
        tables.append(row.table_name)

    table_details = []
    for table in tables:
        fields = cursor.columns(table=table)
        for field in fields:
            table_details.append(
                {
                    "Table": table,
                    "Field": field.column_name,
                    "Data Type": field.type_name,
                    "Nullable": field.is_nullable,
                }
            )

    return pd.DataFrame(table_details)


def get_access_queries(connection):
    """Accessデータベースのクエリ情報を取得する"""
    cursor = connection.cursor()
    queries = []
    for row in cursor.tables(tableType="VIEW"):
        queries.append(row.table_name)

    query_details = []
    for query in queries:
        sql = cursor.execute(
            f"SELECT sql FROM msysobjects WHERE name='{query}'"
        ).fetchone()
        query_details.append({"Query": query, "SQL": sql[0] if sql else "N/A"})

    return pd.DataFrame(query_details)


def save_details_to_excel(table_df, query_df, output_path):
    """テーブルとクエリの詳細をExcelに出力する"""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        table_df.to_excel(writer, sheet_name="Tables", index=False)
        query_df.to_excel(writer, sheet_name="Queries", index=False)


def generate_er_diagram_svg(db_url, output_path):
    """AccessデータベースのスキーマをMermaid記法のER図としてSVG形式で出力する"""
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    graph = create_schema_graph(
        metadata=metadata,
        show_datatypes=False,  # データ型を表示すると画像が大きくなるので非表示
        show_indexes=False,  # インデックスも非表示
        rankdir="LR",  # 左から右への表示
        concentrate=False,  # 関係線をまとめない
    )

    graph.write_svg(output_path)


def main(db_path, excel_output_path, svg_output_path):
    """メイン処理"""
    # Accessデータベースに接続
    connection = connect_to_access(db_path)

    # テーブルとクエリの情報を取得
    table_df = get_access_tables_and_columns(connection)
    query_df = get_access_queries(connection)

    # Excelに出力
    save_details_to_excel(table_df, query_df, excel_output_path)

    # ER図をSVG形式で出力
    db_url = (
        f"access+pyodbc://@/{db_path}?driver=Microsoft Access Driver (*.mdb, *.accdb)"
    )
    generate_er_diagram_svg(db_url, svg_output_path)

    # 接続を閉じる
    connection.close()


# 実行例
db_path = "your_database_path.accdb"
excel_output_path = "access_details.xlsx"
svg_output_path = "dbschema.svg"

main(db_path, excel_output_path, svg_output_path)
