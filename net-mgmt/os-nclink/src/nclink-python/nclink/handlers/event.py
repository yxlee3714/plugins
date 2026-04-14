# nclink/handlers/event.py
from ..pdu.base import NC_PDU
from loguru import logger

def handle_event_register(pdu_dict: dict) -> NC_PDU:
    """Register/Event/Request/dev_uuid - 事件注册"""
    guid = pdu_dict.get("guid", "")
    event_id = pdu_dict.get("id", "")
    logger.info(f"收到事件注册请求: {event_id} (终端: {guid})")
    
    # 实际应分配事件资源并返回事件ID
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"event_id": f"evt_{event_id}"}
    )

def handle_event_data(pdu_dict: dict) -> NC_PDU:
    """Event/dev_uuid/ex_cid - 事件数据推送（订阅/发布模式）"""
    guid = pdu_dict.get("guid", "")
    logger.info("事件被触发，推送数据")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={
            "id": "event_01",
            "time": 1744528800000,
            "event": {"id": "010302", "value": "running", "oldValue": "free"}
        }
    )

def handle_event_unregister(pdu_dict: dict) -> NC_PDU:
    """Unregister/Event/Request/dev_uuid - 事件注销"""
    guid = pdu_dict.get("guid", "")
    event_id = pdu_dict.get("id", "")
    logger.info(f"收到事件注销请求: {event_id}")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK"
    )
