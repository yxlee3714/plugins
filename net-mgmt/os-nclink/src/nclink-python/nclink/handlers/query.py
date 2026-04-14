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
        if isinstance(item, dict):
            item_id = item.get("id")
        else:
            item_id = item   # 处理 ids 是字符串列表的情况（如动态采样误入）

        data_item = model.get_data_item(item_id)
        
        if data_item:
            results.append({
                "id": item_id,
                "value": data_item.value,
                "code": "OK"
            })
        else:
            results.append({
                "id": item_id,
                "code": "NG",
                "reason": "Unavailable",
                "error": 202
            })

    return NC_PDU(
        id=pdu_dict.get("@id", ""),
        guid=guid,
        code="OK",
        privateInfo={"values": results}
    )
