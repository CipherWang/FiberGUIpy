import json
import requests

class FiberRPC:
    def __init__(self, url):
        self.url = url

    def rpc_request(self, method, params=None):
        """
        发起 RPC 请求并返回解析后的 JSON 结果。

        :param url: str, RPC 服务器地址
        :param method: str, RPC 方法名称
        :param params: dict 或 list, RPC 方法的参数
        :return: dict, 返回的 JSON 结果
        """
        if params is None:
            params = {}
        headers = {
            'Content-Type': 'application/json',
        }

        # 构造请求数据
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        code = "error"
        try:
            # 发起 POST 请求
            response = requests.post(self.url,
                                     headers=headers,
                                     data=json.dumps(payload),
                                     timeout=5)

            # 检查 HTTP 状态码
            response.raise_for_status()
            # 解析返回的 JSON 数据
            result = response.json()
            # 检查是否包含错误
            if "error" in result:
                raise ValueError(f"RPC Error: {result['error']}")
            code = "ok"
            data = result.get("result", {})
        except requests.exceptions.RequestException as e:
            data = f"HTTP Error: {e}"
        except ValueError as e:
            data = f"RPC Error: {e}"
        return {"code": code, "data": data}

    def node_info(self):
        return self.rpc_request("node_info")

    def list_channels(self, param):
        return self.rpc_request("list_channels", params=param)