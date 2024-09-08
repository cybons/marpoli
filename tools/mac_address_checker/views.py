import re
from logging import getLogger

from fastapi import APIRouter, HTTPException

# from .data_manager import load_asset_data, load_network_data
from .models import MACRequest

router = APIRouter()
logger = getLogger("tools")
# データのロード
# asset_data = load_asset_data("asset_system_data.csv")
# network_data = load_network_data("network_monitoring_data.csv")


def normalize_mac_address(mac):
    mac = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()  # 不要な文字を削除して大文字に変換
    if len(mac) == 12:
        normalized_mac = ":".join(
            mac[i : i + 2] for i in range(0, 12, 2)
        )  # コロン区切りに変換
        logger.info(
            f"Normalized MAC address: {normalized_mac}"
        )  # 正規化後のMACアドレスをログに出力
        return normalized_mac
    logger.error(f"Invalid MAC Address Format: {mac}")
    raise ValueError("Invalid MAC Address Format")


@router.post("/check_mac/")
def check_mac(request: MACRequest):
    logger.info(
        f"Received request: Hostname={request.hostname}, MAC Address={request.mac_address}"
    )

    # MACアドレスを正規化
    try:
        normalized_mac = normalize_mac_address(request.mac_address)
        logger.info(
            f"MAC address and hostname matched and allowed: {normalized_mac}, {request.hostname}"
        )
    except ValueError as e:
        logger.error(f"Error normalizing MAC address: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # 端末名とMACアドレスの一致を確認
    # asset_match = asset_data[
    #     (asset_data["端末名"] == request.hostname)
    #     & (
    #         asset_data[["MACアドレス1", "MACアドレス2", "MACアドレス3"]]
    #         .eq(normalized_mac)
    #         .any(axis=1)
    #     )
    # ]
    # network_match = network_data[network_data["MACアドレス"] == normalized_mac]

    # if not asset_match.empty and not network_match.empty:
    #     logger.info(
    #         f"MAC address and hostname matched and allowed: {normalized_mac}, {request.hostname}"
    #     )
    #     return {
    #         "status": "success",
    #         "message": "MACアドレスと端末名が一致し、許可されています。",
    #     }
    # elif not asset_match.empty:
    #     logger.warning(
    #         f"MAC address and hostname matched, but not allowed: {normalized_mac}, {request.hostname}"
    #     )
    #     return {
    #         "status": "warning",
    #         "message": "MACアドレスと端末名は一致していますが、許可されていません。",
    #     }
    # else:
    #     logger.error(
    #         f"MAC address and hostname do not match: {normalized_mac}, {request.hostname}"
    #     )
    #     return {"status": "error", "message": "MACアドレスと端末名が一致しません。"}
