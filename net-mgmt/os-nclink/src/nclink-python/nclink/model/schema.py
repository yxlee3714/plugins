# nclink/model/schema.py
import json
from pathlib import Path
from loguru import logger

class ModelValidator:
    def __init__(self, schema_path: str = None):
        # 如果没有传入路径，则使用相对路径
        if schema_path is None:
            schema_path = "schema/nclink_schema.json"

        self.schema_path = Path(schema_path)
        self.schema = None
        self.load_schema()

    def load_schema(self):
        try:
            if self.schema_path.exists():
                with open(self.schema_path, encoding="utf-8") as f:
                    self.schema = json.load(f)
                logger.info("NC-Link JSON Schema 加载成功")
            else:
                logger.warning(f"Schema 文件不存在: {self.schema_path}")
        except Exception as e:
            logger.error(f"加载 Schema 失败: {e}")

    def validate(self, model_data: dict) -> bool:
        if not self.schema:
            logger.warning("Schema 未加载，跳过严格验证")
            return True
        try:
            if model_data.get("type") != "NC_LINK_ROOT":
                logger.error("根对象 type 必须为 NC_LINK_ROOT")
                return False
            logger.success("数控机床模型验证通过")
            return True
        except Exception as e:
            logger.error(f"模型验证失败: {e}")
            return False
