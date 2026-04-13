#!/usr/bin/env python3.11
import asyncio
import sys
import os

# 添加协议栈路径
sys.path.insert(0, "/usr/local/opnsense/src/nclink-python")

from nclink.server import NCLinkServer

async def main():
    # 可通过配置文件修改端口和模型路径（后续版本支持）
    server = NCLinkServer(
        host="0.0.0.0",
        port=8080,
        model_path="/usr/local/etc/nclink/test_model.json"
    )
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
