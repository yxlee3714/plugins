#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版 非MQTT TCP 测试客户端 - 基于附录A & 附录B.1
直接通过 TCP 发送 NC-Link 标准 JSON
"""

import asyncio
import json
import sys
from typing import Dict, Any

HOST = "127.0.0.1"
PORT = 8080
DEVICE_GUID = "dev_uuid_0103"


async def send_request(request: Dict[str, Any], description: str):
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        
        data = json.dumps(request, ensure_ascii=False) + "\n"
        writer.write(data.encode())
        await writer.drain()

        response = await reader.readline()
        resp_text = response.decode().strip()

        print(f"\n{'='*85}")
        print(f"【{description}】")
        print(f"→ 发送: {json.dumps(request, ensure_ascii=False, indent=2)}")
        print(f"← 收到: {resp_text}")
        print(f"{'='*85}\n")

        writer.close()
        await writer.wait_closed()

    except ConnectionRefusedError:
        print(f"❌ 无法连接到 NC-Link 服务 {HOST}:{PORT}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 请求失败: {e}")


async def main():
    print("🚀 NC-Link TCP 最终测试客户端启动（基于附录A & 附录B.1）\n")

    test_cases = [
        ("1. 注册请求", {"@id": "reg001", "cli_uuid": DEVICE_GUID}),
        ("2. 模型版本校对", {"@id": "probe001", "guid": DEVICE_GUID}),
        ("3. 模型侦测", {"@id": "probe002", "guid": DEVICE_GUID}),
        ("4. 数据查询", {
            "@id": "query001",
            "guid": DEVICE_GUID,
            "ids": [{"id": "010302"}, {"id": "010303"}, {"id": "0103080402"}]
        }),
        ("5. 数据采样", {"@id": "sample001", "guid": DEVICE_GUID, "id": "sample_channel0"}),
        ("6. 方法调用", {
            "@id": "method001",
            "guid": DEVICE_GUID,
            "id": "method001",
            "args": {"operation": "push", "source": "/gcodes/O1"}
        }),
        ("7. 事件注册", {
            "@id": "event001",
            "guid": DEVICE_GUID,
            "id": "010302",
            "filters": [{"type": "equal", "value": "running"}],
            "triggerType": "always"
        }),
        ("8. 动态采样注册", {
            "@id": "dyn001",
            "guid": DEVICE_GUID,
            "ids": ["010302", "010303"],
            "sampleInterval": 500,
            "uploadInterval": 2000
        })
    ]

    for desc, payload in test_cases:
        await send_request(payload, desc)

    print("🎉 TCP 测试全部完成！")


if __name__ == "__main__":
    asyncio.run(main())
