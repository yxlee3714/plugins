# nclink/pdu/base.py
from dataclasses import dataclass
import json
from typing import Optional, Dict

@dataclass
class NC_PDU:
    id: str
    guid: str
    code: str = "OK"
    reason: Optional[str] = None
    error: Optional[int] = None
    privateInfo: Optional[Dict] = None

    def to_json(self) -> str:
        data = {
            "@id": self.id,
            "guid": self.guid,
            "code": self.code,
        }
        if self.reason:
            data["reason"] = self.reason
        if self.error is not None:
            data["error"] = self.error
        if self.privateInfo:
            data["privateInfo"] = self.privateInfo
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("@id", ""),
            guid=data.get("guid") or data.get("cli_uuid", ""),
            code=data.get("code", "OK"),
            reason=data.get("reason"),
            error=data.get("error"),
            privateInfo=data.get("privateInfo")
        )
