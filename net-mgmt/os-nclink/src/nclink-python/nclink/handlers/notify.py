# nclink/handlers/notify.py
from ..pdu.base import NC_PDU
from loguru import logger

def handle_notify(pdu_dict: dict) -> NC_PDU:
    """处理状态通知（Notify/State）"""
    guid = pdu_dict.get("guid", "")
    
    logger.info(f"收到状态通知请求，终端: {guid}")

    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"status": "online"}
    )
