import os
import re
import sqlite3
from datetime import datetime, timedelta

import feedparser
import pandas as pd
import yaml


def create_db(db_path):
    """データベースを作成します。既に存在する場合は何もしません。"""
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                site_name TEXT,
                title TEXT,
                link TEXT UNIQUE,
                post_date TEXT,
                save_date TEXT,
                is_matched INTEGER
            )
        """)
        conn.commit()
        conn.close()


def save_article(db_path, site_name, title, link, post_date, is_matched):
    """記事をデータベースに保存します。保存時間も記録します。"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    save_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        c.execute(
            "INSERT INTO articles (site_name, title, link, post_date, save_date, is_matched) VALUES (?, ?, ?, ?, ?, ?)",
            (site_name, title, link, post_date, save_date, is_matched),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def fetch_rss_articles(sites, common_keywords, common_regexes, db_path="articles.db"):
    """RSSフィードから記事を取得し、データベースに保存します。"""
    create_db(db_path)
    new_articles = []

    for site in sites:
        site_name = site["name"]
        rss_url = site["url"]
        site_keywords = site.get("keywords", [])
        site_regexes = site.get("regexes", [])

        keywords = site_keywords + common_keywords
        regexes = site_regexes + common_regexes

        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            post_date = entry.published

            # タイトルとキーワードを小文字に変換して比較
            title_lower = title.lower()
            is_matched = 0
            if any(keyword.lower() in title_lower for keyword in keywords) or any(
                re.search(regex, title, re.IGNORECASE) for regex in regexes
            ):
                is_matched = 1

            if save_article(db_path, site_name, title, link, post_date, is_matched):
                new_articles.append(
                    {
                        "site_name": site_name,
                        "title": title,
                        "link": link,
                        "post_date": post_date,
                        "is_matched": is_matched,
                    }
                )

    return new_articles


def get_recent_articles(db_path, days, matched_only=True):
    """直近n日分の記事を取得します。デフォルトではマッチした記事のみを取得します。"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    date_threshold = datetime.now() - timedelta(days=days)
    date_threshold_str = date_threshold.strftime("%Y-%m-%dT%H:%M:%S")

    if matched_only:
        c.execute(
            "SELECT * FROM articles WHERE post_date >= ? AND is_matched = 1",
            (date_threshold_str,),
        )
    else:
        c.execute("SELECT * FROM articles WHERE post_date >= ?", (date_threshold_str,))

    articles = c.fetchall()
    conn.close()
    return articles


def export_articles_to_excel(articles, output_file):
    """記事をExcelファイルにエクスポートします。"""
    df = pd.DataFrame(
        articles,
        columns=[
            "ID",
            "Site Name",
            "Title",
            "Link",
            "Post Date",
            "Save Date",
            "Is Matched",
        ],
    )
    df.to_excel(output_file, index=False)


def main():
    """主要な処理を行うメイン関数です。"""
    current_path = os.path.dirname(__file__)
    # YAMLファイルからサイト定義を読み込み
    with open(os.path.join(current_path, "sites.yaml"), "r", encoding="utf8") as f:
        config = yaml.safe_load(f)

    sites = config["sites"]
    common_keywords = config["common_keywords"]
    common_regexes = config["common_regexes"]

    db_path = "articles.db"
    rss = fetch_rss_articles(sites, common_keywords, common_regexes, db_path)
    print(rss)

    # 直近7日分の記事を取得
    recent_articles = get_recent_articles(db_path, days=7)

    # Excelにエクスポート
    export_articles_to_excel(recent_articles, "recent_articles.xlsx")

    print("Recent articles exported to recent_articles.xlsx")


if __name__ == "__main__":
    main()
