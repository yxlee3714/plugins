#!/usr/local/bin/python3

import socket
import threading
import json
import time
import traceback

# =========================
# 全局设备池（线程安全）
# =========================
devices = {}
lock = threading.Lock()

# =========================
# NC-Link → 标准模型映射
# =========================
def map_nclink_to_model(msg):
    model = {}

    try:
        data = msg.get("data", {})
        device_id = msg.get("deviceId")

        # ========= device =========
        model["device"] = {
            "id": device_id,
            "name": data.get("deviceName", ""),
            "type": data.get("deviceType", ""),
            "vendor": data.get("vendor", ""),
            "model": data.get("model", ""),
            "serial": data.get("serialNumber", "")
        }

        # ========= status =========
        model["status"] = {
            "mode": data.get("mode", "UNKNOWN"),
            "run": data.get("status", "UNKNOWN"),
            "power": data.get("power", "ON"),
            "emergency": data.get("emergency", False)
        }

        # ========= process =========
        model["process"] = {
            "program": data.get("program", ""),
            "line": data.get("line", 0),
            "spindle_speed": data.get("spindleSpeed", 0),
            "spindle_load": data.get("spindleLoad", 0),
            "feed_rate": data.get("feedRate", 0),
            "override": {
                "feed": data.get("feedOverride", 100),
                "spindle": data.get("spindleOverride", 100)
            }
        }

        # ========= axis =========
        axis_data = data.get("axis", {})
        model["axis"] = {}

        for axis in ["X", "Y", "Z", "A", "B", "C"]:
            model["axis"][axis] = {
                "pos": axis_data.get(axis, 0),
                "load": data.get(f"{axis}_load", 0)
            }

        # ========= alarm =========
        alarms = data.get("alarm", [])
        model["alarm"] = []

        for a in alarms:
            model["alarm"].append({
                "code": a.get("code", ""),
                "level": a.get("level", "INFO"),
                "message": a.get("msg", ""),
                "time": a.get("time", int(time.time()))
            })

        # ========= meta =========
        model["meta"] = {
            "timestamp": msg.get("timestamp", int(time.time())),
            "source": "nclink",
            "raw": msg
        }

    except Exception as e:
        print("[!] Mapping error:", e)
        traceback.print_exc()

    return model


# =========================
# 数据校验
# =========================
def validate_model(model):
    errors = []

    try:
        if not model["device"]["id"]:
            errors.append("deviceId missing")

        if model["process"]["spindle_speed"] < 0:
            errors.append("invalid spindle speed")

        if model["process"]["feed_rate"] < 0:
            errors.append("invalid feed rate")

        for axis, val in model["axis"].items():
            if not isinstance(val["pos"], (int, float)):
                errors.append(f"{axis} position invalid")

    except Exception as e:
        errors.append(f"validation exception: {e}")

    return errors


# =========================
# 注册设备
# =========================
def handle_register(msg):
    device_id = msg.get("data", {}).get("deviceId")

    if not device_id:
        return

    with lock:
        devices[device_id] = {
            "device": {"id": device_id},
            "status": {"run": "ONLINE"},
            "meta": {"timestamp": int(time.time())}
        }

    print(f"[+] Device registered: {device_id}")


# =========================
# 处理数据
# =========================
def handle_data(msg):
    model = map_nclink_to_model(msg)
    errors = validate_model(model)

    if errors:
        print("[!] Validation failed:", errors)
        return

    device_id = model["device"]["id"]

    with lock:
        devices[device_id] = model


# =========================
# 客户端处理（支持粘包）
# =========================
def handle_client(conn, addr):
    print(f"[+] Connected: {addr}")

    buffer = b""

    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                break

            buffer += chunk

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if not line.strip():
                    continue

                msg = json.loads(line.decode())

                msg_type = msg.get("type")

                if msg_type == "register":
                    handle_register(msg)

                elif msg_type == "data":
                    handle_data(msg)

                else:
                    print("[!] Unknown message type:", msg_type)

        except Exception as e:
            print("[!] Client error:", e)
            traceback.print_exc()
            break

    conn.close()
    print(f"[-] Disconnected: {addr}")


# =========================
# TCP Server
# =========================
def start_server(host="0.0.0.0", port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen(10)

    print(f"[*] NC-Link agent running on {host}:{port}")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.daemon = True
        t.start()


# =========================
# 状态输出（API调用）
# =========================
def status():
    with lock:
        print(json.dumps(devices))


# =========================
# 主入口
# =========================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            status()
        else:
            print("Unknown command")

    else:
        start_server()
