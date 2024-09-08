import logging
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler


def set_logger():
    # 全体のログ設定
    # ファイルに書き出す。ログが100KB溜まったらバックアップにして新しいファイルを作る。

    # デバッグ時と運用時でログレベルを切り替える
    if __debug__:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.WARNING

    # # ログフォーマットの定義
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # プロジェクトルート名を指定したロガーの作成
    logger = logging.getLogger("tools")
    logger.setLevel(logging.DEBUG)  # Logger全体のレベルをDEBUGに設定

    # RichHandlerの追加
    console_handler = RichHandler(level=LOG_LEVEL, rich_tracebacks=True)
    # console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    # ファイルハンドラを追加（必要に応じて）
    file_handler = RotatingFileHandler(
        "logs/tools.log", maxBytes=100 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)  # ファイルには常にDEBUGレベルで記録
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    return logger
