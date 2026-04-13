# nclink/handlers/sample.py
from ..pdu.base import NC_PDU
from ..model.types import NCModel
from loguru import logger

def handle_sample(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理数据采样（Sample）—— 简化返回示例组合数据"""
    guid = pdu_dict.get("guid", "")
    channel_id = pdu_dict.get("id", "default")

    logger.info(f"收到采样请求，通道: {channel_id}")

    # 实际应根据采样通道 ids 采集真实数据，这里返回示例
    sample_data = [
        [100.5, 200.0, 10.2],   # 示例：位置、速度、电流
        [105.0, 205.5, 10.8]
    ]

    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={
            "id": channel_id,
            "data": sample_data
        }
    )
