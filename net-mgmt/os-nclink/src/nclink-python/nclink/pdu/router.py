# nclink/pdu/router.py
import json
from loguru import logger
from ..pdu.base import NC_PDU
from ..pdu.errors import NCError

from ..handlers.register import handle_register
from ..handlers.probe import handle_probe_version, handle_probe_query, handle_probe_set
from ..handlers.query import handle_query
from ..handlers.sample import handle_sample
from ..handlers.notify import handle_notify
from ..handlers.method import (
    handle_method_call, handle_method_status, 
    handle_method_result, handle_method_control
)
from ..handlers.event import (
    handle_event_register, handle_event_data, handle_event_unregister
)
from ..handlers.dynamic_sample import (
    handle_dynamic_sample_register,
    handle_dynamic_sample_data,
    handle_dynamic_sample_unregister
)

class Router:
    def __init__(self, model):
        self.model = model

    async def route(self, pdu_dict: dict) -> str:
        try:
            msg_id = pdu_dict.get("@id", "")
            guid = pdu_dict.get("guid") or pdu_dict.get("cli_uuid", "")
            cmd_lower = json.dumps(pdu_dict).lower()

            logger.debug(f"收到请求 @id={msg_id}, guid={guid}, keys={list(pdu_dict.keys())}")

            # ==================== 精确路由逻辑 ====================
            if "cli_uuid" in pdu_dict or msg_id.startswith("reg"):
                resp = handle_register(pdu_dict, self.model)

            # Probe/Version
            elif msg_id.startswith("probe") and "version" in cmd_lower or "version" in pdu_dict:
                resp = handle_probe_version(pdu_dict, self.model)

            # Probe/Query
            elif msg_id.startswith("probe") and "query" in cmd_lower or ("probe" in cmd_lower and "query" in cmd_lower):
                resp = handle_probe_query(pdu_dict, self.model)

            # Probe/Set
            elif "probe/set" in cmd_lower:
                resp = handle_probe_set(pdu_dict, self.model)

            # Query/Request
            elif "ids" in pdu_dict and isinstance(pdu_dict.get("ids"), list):
                resp = handle_query(pdu_dict, self.model)

            # Sample
            elif "sample" in cmd_lower or (msg_id.startswith("sample") and "id" in pdu_dict):
                resp = handle_sample(pdu_dict, self.model)

            # Notify
            elif "notify" in cmd_lower or "state" in cmd_lower:
                resp = handle_notify(pdu_dict)

            # Method
            elif "method" in cmd_lower:
                if "call" in cmd_lower:
                    resp = handle_method_call(pdu_dict)
                elif "status" in cmd_lower:
                    resp = handle_method_status(pdu_dict)
                elif "result" in cmd_lower:
                    resp = handle_method_result(pdu_dict)
                elif "control" in cmd_lower:
                    resp = handle_method_control(pdu_dict)
                else:
                    resp = handle_method_call(pdu_dict)

            # Event
            elif "event" in cmd_lower:
                if "register" in cmd_lower:
                    resp = handle_event_register(pdu_dict)
                elif "unregister" in cmd_lower:
                    resp = handle_event_unregister(pdu_dict)
                else:
                    resp = handle_event_data(pdu_dict)

            # Dynamic Sample
            elif "dynamic" in cmd_lower and "sample" in cmd_lower:
                if "register" in cmd_lower:
                    resp = handle_dynamic_sample_register(pdu_dict)
                elif "unregister" in cmd_lower:
                    resp = handle_dynamic_sample_unregister(pdu_dict)
                else:
                    resp = handle_dynamic_sample_data(pdu_dict)

            else:
                logger.warning(f"无法匹配的请求: {pdu_dict}")
                raise NCError(401, f"未知指令: {msg_id}")

            return resp.to_json()

        except NCError as e:
            err = NC_PDU(
                id=pdu_dict.get("@id", "unknown"),
                guid=guid,
                code="NG",
                reason=e.reason,
                error=e.code
            )
            return err.to_json()
        except Exception as e:
            logger.exception("路由处理异常")
            err = NC_PDU(
                id=pdu_dict.get("@id", ""),
                guid=guid,
                code="NG",
                reason="Internal Error"
            )
            return err.to_json()
