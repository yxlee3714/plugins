# nclink/pdu/router.py
import json
from loguru import logger
from .base import NC_PDU
from .errors import NCError
from ..handlers.register import handle_register
from ..handlers.probe import handle_probe_version, handle_probe_query, handle_probe_set
from ..handlers.query import handle_query
from ..handlers.sample import handle_sample
from ..handlers.notify import handle_notify
from ..model.types import NCModel

class Router:
    def __init__(self, model: NCModel):
        self.model = model

    async def route(self, pdu_dict: dict) -> str:
        try:
            # 根据标准指令关键字路由（简化版，可后续扩展为精确匹配）
            cmd_str = json.dumps(pdu_dict)

            if "Register/Request" in cmd_str or "cli_uuid" in pdu_dict:
                resp = handle_register(pdu_dict, self.model)
            elif "Probe/Version" in cmd_str:
                resp = handle_probe_version(pdu_dict, self.model)
            elif "Probe/Query" in cmd_str:
                resp = handle_probe_query(pdu_dict, self.model)
            elif "Probe/Set" in cmd_str:
                resp = handle_probe_set(pdu_dict, self.model)
            elif "Query/Request" in cmd_str:
                resp = handle_query(pdu_dict, self.model)
            elif "Sample" in cmd_str:
                resp = handle_sample(pdu_dict, self.model)
            elif "Notify/State" in cmd_str:
                resp = handle_notify(pdu_dict)
            else:
                raise NCError(401, "未知或不支持的指令")

            return resp.to_json()

        except NCError as e:
            err = NC_PDU(
                id=pdu_dict.get("@id", "unknown"),
                guid=pdu_dict.get("guid") or pdu_dict.get("cli_uuid", ""),
                code="NG",
                reason=e.reason,
                error=e.code
            )
            return err.to_json()
        except Exception as e:
            logger.exception("路由处理异常")
            err = NC_PDU(id=pdu_dict.get("@id", ""), guid="", code="NG", reason="Internal Server Error")
            return err.to_json()
