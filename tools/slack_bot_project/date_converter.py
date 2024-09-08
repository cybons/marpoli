from datetime import datetime

from dateutil import parser


def convert_to_google_calendar_format(str_date: str) -> str:
    """
    任意の日付文字列をGoogleカレンダーのISO 8601形式に変換します。
    変換できない場合はValueErrorをスローします。

    Args:
        str_date (str): 変換したい日付文字列

    Returns:
        str: Googleカレンダー用のISO 8601形式の日付文字列
    """
    try:
        # 日付文字列を自動解析してdatetimeオブジェクトに変換
        date_obj = parser.parse(str_date)

        # Googleカレンダー用のISO 8601形式に変換
        iso_format_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return iso_format_date

    except (ValueError, OverflowError) as e:
        raise ValueError(
            f"日付の変換に失敗しました: {str_date}. エラー: {str(e)}"
        ) from e


def convert_to_custom_format(str_date: str, date_format: str) -> str:
    """
    任意の日付文字列を指定されたフォーマットに変換します。
    変換できない場合はValueErrorをスローします。

    Args:
        str_date (str): 変換したい日付文字列
        date_format (str): 変換後の日付フォーマット（例: "%Y/%m/%d", "%d-%m-%Y %H:%M"など）

    Returns:
        str: 指定されたフォーマットの日付文字列
    """
    try:
        # 日付文字列を自動解析してdatetimeオブジェクトに変換
        date_obj = parser.parse(str_date)

        # 指定されたフォーマットの日付文字列に変換
        custom_format_date = date_obj.strftime(date_format)
        return custom_format_date

    except (ValueError, OverflowError) as e:
        raise ValueError(
            f"日付の変換に失敗しました: {str_date} (フォーマット: {date_format}). エラー: {str(e)}"
        ) from e


def convert_from_format_to_format(
    str_date: str, from_format: str, to_format: str
) -> str:
    """
    任意の日付文字列を指定されたフォーマットで解析し、別のフォーマットに変換します。
    変換できない場合はValueErrorをスローします。

    Args:
        str_date (str): 変換したい日付文字列
        from_format (str): 解析に使用する日付フォーマット（例: "%Y/%m/%d"）
        to_format (str): 変換後の日付フォーマット（例: "%d-%m-%Y"）

    Returns:
        str: 指定されたフォーマットに変換された日付文字列
    """
    try:
        # 指定されたフォーマットで日付文字列をdatetimeオブジェクトに変換
        date_obj = datetime.strptime(str_date, from_format)

        # 変換後のフォーマットの日付文字列に変換
        converted_date = date_obj.strftime(to_format)
        return converted_date

    except ValueError as e:
        raise ValueError(
            f"日付の変換に失敗しました: {str_date} (from: {from_format}, to: {to_format}). エラー: {str(e)}"
        ) from e
