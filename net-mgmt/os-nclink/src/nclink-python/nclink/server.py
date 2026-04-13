# nclink/server.py
import asyncio
import json
from loguru import logger
from .pdu.router import Router
from .model.probe import load_model

class NCLinkServer:
    def __init__(self, host="0.0.0.0", port=8080, model_path="/usr/local/etc/nclink/model.json"):
        self.host = host
        self.port = port
        self.model = load_model(model_path)
        self.router = Router(self.model)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"NC-Link 客户端连接: {addr}")

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
                    response = await self.router.route(pdu_dict)
                    writer.write((response + "\n").encode())
                    await writer.drain()
                except json.JSONDecodeError:
                    logger.error("收到无效 JSON")
                except Exception as e:
                    logger.error(f"处理 PDU 失败: {e}")

        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"客户端断开: {addr}")

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.success(f"NC-Link 服务已启动，监听 {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
