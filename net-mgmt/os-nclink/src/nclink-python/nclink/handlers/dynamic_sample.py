# nclink/handlers/dynamic_sample.py
from ..pdu.base import NC_PDU
from loguru import logger

def handle_dynamic_sample_register(pdu_dict: dict) -> NC_PDU:
    """Register/Sample/Request/dev_uuid - 动态采样注册"""
    guid = pdu_dict.get("guid", "")
    logger.info("收到动态采样注册请求")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"dynamic_channel_id": "dyn_sample_001"}
    )

def handle_dynamic_sample_data(pdu_dict: dict) -> NC_PDU:
    """动态数据采样推送（订阅/发布模式）"""
    guid = pdu_dict.get("guid", "")
    logger.info("推送动态采样数据")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={
            "id": "dyn_sample_001",
            "data": [[123.4, 567.8], [124.5, 568.9]]
        }
    )

def handle_dynamic_sample_unregister(pdu_dict: dict) -> NC_PDU:
    """Unregister/Sample/Request/dev_uuid - 动态采样注销"""
    guid = pdu_dict.get("guid", "")
    logger.info("收到动态采样注销请求")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK"
    )
