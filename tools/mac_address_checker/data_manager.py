import pandas as pd


def load_asset_data(file_path: str):
    """
    資産管理システムのデータを読み込み、重複を削除する。
    """
    asset_data = pd.read_csv(file_path)
    asset_data.drop_duplicates(
        subset=["MACアドレス1", "MACアドレス2", "MACアドレス3"], inplace=True
    )
    return asset_data


def load_network_data(file_path: str):
    """
    ネットワーク監視ツールのデータを読み込み、許可済みMACアドレスをマークする。
    """
    network_data = pd.read_csv(file_path)
    network_data["許可済み"] = network_data["MACアドレス"].apply(
        lambda x: check_permission(x)
    )
    return network_data


def check_permission(mac_address):
    """
    許可済みMACアドレスをチェックする。
    """
    allowed_macs = pd.read_csv("allowed_mac_addresses.csv")
    return mac_address in allowed_macs["MACアドレス"].values
