# nclink/server.py
import asyncio
import json
import sys
from loguru import logger

# ====================== 强制日志输出到终端 ======================
logger.remove()  # 移除所有默认处理器
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}",
    colorize=True
)
logger.add(
    "nclink.log", 
    rotation="10 MB", 
    level="DEBUG"
)
# ============================================================

from .pdu.router import Router
from .model.probe import load_model


class NCLinkServer:
    def __init__(self, host="0.0.0.0", port=8080, model_path="tests/test_model.json"):
        logger.info(f"正在初始化 NC-Link 服务，模型路径: {model_path}")
        self.host = host
        self.port = port
        self.model = load_model(model_path)
        self.router = Router(self.model)
        logger.success(f"NC-Link 服务初始化完成，监听地址 {host}:{port}")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"客户端连接: {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                message = data.decode().strip()
                if not message:
                    continue

                try:
                    pdu_dict = json.loads(message)
                    logger.debug(f"收到 PDU: {pdu_dict}")
                    response = await self.router.route(pdu_dict)
                    if response:
                        writer.write((response + "\n").encode())
                        await writer.drain()
                except Exception as e:
                    logger.error(f"处理 PDU 失败: {e}")

        except Exception as e:
            logger.error(f"客户端处理异常: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"客户端断开: {addr}")

    async def start(self):
        logger.success(f"NC-Link 服务启动成功，监听 {self.host}:{self.port}")
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    try:
        logger.info("开始启动 NC-Link 服务...")
        server = NCLinkServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("服务被用户中断 (Ctrl+C)")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        import traceback
        traceback.print_exc()
