# nclink/handlers/probe.py
from ..pdu.base import NC_PDU
from ..model.types import NCModel
from loguru import logger

def handle_probe_version(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理版本号校对请求 Probe/Version"""
    version = model.root.get("version", "1.1.0")
    guid = pdu_dict.get("guid", "")
    
    logger.info(f"收到版本号校对请求，当前模型版本: {version}")
    
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"version": version}
    )

def handle_probe_query(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理模型侦测请求 Probe/Query"""
    guid = pdu_dict.get("guid", "")
    
    logger.info(f"收到模型侦测请求，返回完整模型")
    
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"probe": model.root}
    )

def handle_probe_set(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理模型设置请求 Probe/Set（简化版）"""
    guid = pdu_dict.get("guid", "")
    logger.info(f"收到模型设置请求（当前仅记录，未实际更新模型）")
    
    # 实际生产中应验证新模型并更新
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK"
    )
