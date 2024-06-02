import os

from playwright.sync_api import sync_playwright


def run(playwright):
    path = os.path.join(os.getcwd(), "profile")
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=path,
        channel="chrome",  # または 'msedge'
        headless=False,
    )
    page = browser.new_page()
    # page = browser.new_page()
    # ユーザーエージェントを設定

    # ログインページにアクセス
    page.goto("https://accounts.google.com/signin")

    # メールアドレスを入力して「次へ」をクリック
    page.fill('input[type="email"]', "")
    page.click("#identifierNext")

    # パスワード入力フィールドが表示されるのを待機
    page.wait_for_selector('input[type="password"]', timeout=60000)

    # パスワードを入力して「次へ」をクリック
    page.fill('input[type="password"]', "your_password")
    page.click("#passwordNext")

    # 2ファクタ認証ページで人間が操作するために60秒間待機
    page.wait_for_selector("#2fa-element", timeout=60000)  # ここで手動で操作

    # 2ファクタ認証が完了した後、次のページを待機
    page.wait_for_navigation()

    # ログインセッションを保持したままスクレイピング
    page.goto("https://example.com/some_page")
    print(page.content())

    browser.close()


with sync_playwright() as playwright:
    run(playwright)
