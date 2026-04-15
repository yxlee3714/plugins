# nclink/server_mqtt.py
import asyncio
import json
import threading
from loguru import logger
import paho.mqtt.client as mqtt

from nclink.pdu.router import Router
from nclink.model.probe import load_model


class NCLinkMQTTServer:
    def __init__(self, broker_host="127.0.0.1", broker_port=1883, 
                 nclink_port=8090, model_path="tests/test_model.json"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.nclink_port = nclink_port
        self.model = load_model(model_path)
        self.router = Router(self.model)
        
        self.loop = None
        self.mqtt_client = None
        self.running = True

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.success(f"✅ MQTT 客户端已连接到 Broker {self.broker_host}:{self.broker_port}")
            client.subscribe("nclink/#")   # 订阅所有 nclink 相关 topic
            logger.info("已订阅 Topic: nclink/#")
        else:
            logger.error(f"❌ MQTT 连接失败，代码: {rc}")

    def on_message(self, client, userdata, message):
        """MQTT 消息回调 - 安全地投递到 asyncio loop"""
        try:
            payload = json.loads(message.payload.decode())
            nc_link_request = payload.get("payload") if isinstance(payload, dict) else payload

            if not nc_link_request:
                logger.warning("收到无效 MQTT payload")
                return

            logger.info(f"收到 MQTT 消息 → Topic: {message.topic}")

            # 安全地将任务提交到 asyncio loop
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.process_message(nc_link_request), 
                    self.loop
                )
            else:
                logger.error("asyncio event loop 未运行")

        except json.JSONDecodeError:
            logger.error(f"无效 JSON: {message.payload[:200]}")
        except Exception as e:
            logger.exception(f"消息处理异常: {e}")

    async def process_message(self, nc_link_request: dict):
        """在 asyncio 中处理 NC-Link 请求"""
        try:
            response = await self.router.route(nc_link_request)
            logger.info(f"NC-Link 处理完成，返回: {response[:200]}...")
            # 这里可以后续添加返回给 MQTT 的逻辑（目前只记录）
        except Exception as e:
            logger.exception(f"处理 NC-Link 请求失败: {e}")

    def start_mqtt(self):
        """启动 MQTT 客户端"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        try:
            self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
            self.mqtt_client.loop_forever()
        except Exception as e:
            logger.error(f"MQTT 连接异常: {e}")

    def start(self):
        """启动整个服务"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        logger.info(f"开始启动 NC-Link MQTT 服务，Broker: {self.broker_host}:{self.broker_port}")

        # 在单独线程中运行 MQTT 客户端
        mqtt_thread = threading.Thread(target=self.start_mqtt, daemon=True)
        mqtt_thread.start()

        try:
            # 保持主线程运行
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("服务被用户中断 (Ctrl+C)")
        finally:
            self.running = False
            if self.loop:
                self.loop.stop()


if __name__ == "__main__":
    server = NCLinkMQTTServer()
    server.start()
