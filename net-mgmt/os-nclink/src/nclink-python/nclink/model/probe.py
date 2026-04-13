# nclink/model/probe.py
import json
from pathlib import Path
from loguru import logger
from .types import NCModel
from .schema import ModelValidator

def load_model(model_path: str = "/usr/local/etc/nclink/model.json") -> NCModel:
    """加载数控机床模型文件"""
    try:
        path = Path(model_path)
        if not path.exists():
            logger.warning(f"模型文件不存在: {model_path}，使用空模型")
            return NCModel({"id": "default", "type": "NC_LINK_ROOT", "version": "1.1.0", "devices": []})

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        validator = ModelValidator()
        if not validator.validate(data):
            logger.warning("模型验证不通过，仍尝试加载")

        model = NCModel(data)
        logger.success(f"NC-Link 模型加载成功，设备数量: {len(model.devices)}")
        return model

    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        return NCModel({"id": "error", "type": "NC_LINK_ROOT", "version": "1.0", "devices": []})
