# nclink/handlers/query.py
from ..pdu.base import NC_PDU
from ..model.types import NCModel
from loguru import logger

def handle_query(pdu_dict: dict, model: NCModel) -> NC_PDU:
    """处理数据查询请求 Query/Request"""
    ids = pdu_dict.get("ids", [])
    guid = pdu_dict.get("guid", "")
    results = []

    logger.info(f"收到数据查询请求，查询 {len(ids)} 个数据项")

    for item in ids:
        item_id = item.get("id")
        data_item = model.get_data_item(item_id)
        
        if data_item:
            results.append({
                "id": item_id,
                "value": data_item.value,
                "code": "OK"
            })
            logger.debug(f"查询成功: {item_id} = {data_item.value}")
        else:
            results.append({
                "id": item_id,
                "code": "NG",
                "reason": "Unavailable",
                "error": 202
            })
            logger.warning(f"数据项不存在: {item_id}")

    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"values": results}
    )
