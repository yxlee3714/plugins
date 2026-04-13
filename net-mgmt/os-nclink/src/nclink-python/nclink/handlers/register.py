# nclink/handlers/register.py
from ..pdu.base import NC_PDU
from ..model.types import NCModel
from loguru import logger

def handle_register(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理注册请求（适配器或应用系统向代理器注册）"""
    cli_uuid = pdu_dict.get("cli_uuid") or pdu_dict.get("guid", "")
    
    logger.info(f"收到注册请求，终端标识符: {cli_uuid}")
    
    # 标准中注册成功返回 OK
    return NC_PDU(
        id=pdu_dict.get("@id", "reg_unknown"),
        guid=cli_uuid,
        code="OK"
    )
