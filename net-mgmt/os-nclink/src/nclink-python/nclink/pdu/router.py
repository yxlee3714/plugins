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
            at_id = str(pdu_dict.get("@id", "")).lower()
            guid = pdu_dict.get("guid") or pdu_dict.get("cli_uuid", "")
            
            logger.debug(f"路由收到请求 → @id={at_id}, guid={guid}")

            # ==================== 简单清晰的路由 ====================

            if at_id.startswith("reg") or "cli_uuid" in pdu_dict:
                resp = handle_register(pdu_dict, self.model)

            # Probe 系列（最常见的问题点）
            elif at_id.startswith("probe"):
                if "version" in at_id or "version" in str(pdu_dict).lower():
                    resp = handle_probe_version(pdu_dict, self.model)
                elif "query" in at_id or "query" in str(pdu_dict).lower():
                    resp = handle_probe_query(pdu_dict, self.model)
                elif "set" in at_id:
                    resp = handle_probe_set(pdu_dict, self.model)
                else:
                    # 默认当作 Probe/Query 处理（最常见情况）
                    resp = handle_probe_query(pdu_dict, self.model)

            elif "ids" in pdu_dict and isinstance(pdu_dict.get("ids"), list):
                resp = handle_query(pdu_dict, self.model)

            elif at_id.startswith("sample") or "sample" in at_id:
                resp = handle_sample(pdu_dict, self.model)

            elif "notify" in at_id or "state" in at_id:
                resp = handle_notify(pdu_dict)

            # Method
            elif at_id.startswith("method") or "method" in at_id:
                if "call" in at_id:
                    resp = handle_method_call(pdu_dict)
                elif "status" in at_id:
                    resp = handle_method_status(pdu_dict)
                elif "result" in at_id:
                    resp = handle_method_result(pdu_dict)
                elif "control" in at_id:
                    resp = handle_method_control(pdu_dict)
                else:
                    resp = handle_method_call(pdu_dict)

            # Event
            elif at_id.startswith("event") or "event" in at_id:
                if "register" in at_id:
                    resp = handle_event_register(pdu_dict)
                elif "unregister" in at_id:
                    resp = handle_event_unregister(pdu_dict)
                else:
                    resp = handle_event_data(pdu_dict)

            # Dynamic Sample
            elif "dynamic" in at_id or ("dyn" in at_id and "sample" in at_id):
                if "register" in at_id:
                    resp = handle_dynamic_sample_register(pdu_dict)
                elif "unregister" in at_id:
                    resp = handle_dynamic_sample_unregister(pdu_dict)
                else:
                    resp = handle_dynamic_sample_data(pdu_dict)

            else:
                logger.warning(f"无法匹配的请求 → @id={at_id} | 完整内容: {pdu_dict}")
                raise NCError(401, f"未知指令: {at_id}")

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
