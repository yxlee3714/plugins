# nclink/handlers/method.py
from ..pdu.base import NC_PDU
from loguru import logger

def handle_method_call(pdu_dict: dict) -> NC_PDU:
    """Method/Call/dev_uuid - 调用方法"""
    guid = pdu_dict.get("guid", "")
    method_id = pdu_dict.get("id", "")
    logger.info(f"收到方法调用请求: {method_id} (终端: {guid})")
    
    # 这里可接入真实方法执行逻辑，当前返回成功
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"method_id": method_id, "status": "executing"}
    )

def handle_method_status(pdu_dict: dict) -> NC_PDU:
    """Method/Status/dev_uuid - 方法执行进度"""
    guid = pdu_dict.get("guid", "")
    logger.info("收到方法进度查询")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"progress": 75, "message": "Executing..."}
    )

def handle_method_result(pdu_dict: dict) -> NC_PDU:
    """Method/Result/dev_uuid - 方法执行结果"""
    guid = pdu_dict.get("guid", "")
    logger.info("收到方法结果查询")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"result": "success", "output": "Operation completed"}
    )

def handle_method_control(pdu_dict: dict) -> NC_PDU:
    """Method/Control/Request/dev_uuid - 方法控制（stop/resume/cancel）"""
    guid = pdu_dict.get("guid", "")
    action = pdu_dict.get("action", "")
    logger.info(f"收到方法控制指令: {action}")
    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK"
    )
