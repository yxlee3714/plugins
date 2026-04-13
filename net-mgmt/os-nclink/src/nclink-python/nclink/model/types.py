# nclink/model/types.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class DataItem:
    id: str
    type: str
    name: Optional[str] = None
    value: Any = None
    datatype: Optional[str] = None
    setable: bool = False

class NCModel:
    def __init__(self, data: dict):
        self.root = data
        self.devices = data.get("devices", [])

    def get_data_item(self, item_id: str) -> Optional[DataItem]:
        """根据 id 查找数据项"""
        for dev in self.devices:
            # 查找设备层 dataItems
            for item in dev.get("dataItems", []):
                if item.get("id") == item_id:
                    return DataItem(**{k: v for k, v in item.items() if k in DataItem.__annotations__})
            # 查找组件层 dataItems
            for comp in dev.get("components", []):
                for item in comp.get("dataItems", []):
                    if item.get("id") == item_id:
                        return DataItem(**{k: v for k, v in item.items() if k in DataItem.__annotations__})
        return None
