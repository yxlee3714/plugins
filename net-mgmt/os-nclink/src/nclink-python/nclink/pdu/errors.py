# nclink/pdu/errors.py
class NCError(Exception):
    def __init__(self, code: int, reason: str = None):
        self.code = code
        self.reason = reason or "Unknown Error"
        super().__init__(f"NC-Link Error {code}: {self.reason}")

# 常用错误码（根据标准表19）
ERROR_MESSAGES = {
    0: "Success",
    101: "Out of Range",
    102: "Parameter Missing",
    201: "Network Failed",
    202: "Unavailable",
    203: "Timeout",
    301: "Permission Denied",
    401: "Node not exists",
    402: "No index passed in",
    403: "No key passed in",
    404: "Memory configured error",
    405: "Value type error",
    406: "unsupported operation get_length",
    407: "unsupported operation get_attributes",
    408: "unsupported operation get_keys",
    409: "arguments nimiety",
    410: "key error",
    411: "Attribute error",
    412: "syntax error",
    413: "keys of arguments error",
    414: "unsupported terminal identifier",
    415: "Insufficient dynamic sampling resources",
    416: "Insufficient event resources",
    417: "Insufficient method resources",
    418: "method action type error",
    419: "filter type error",
    420: "trigger type error",
    421: "filter type and arguments not matched",
}
