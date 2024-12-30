import json
import secrets

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
            print(result)
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

    def open_channel(self, peer_id, funding_amount, funding_udt_type_script=None):
        return self.rpc_request("open_channel",
                                params=[{"peer_id":peer_id,
                                         "funding_amount":hex(int(funding_amount*10**8))}])

    def shutdown_channel(self, chn_id):
        return self.rpc_request("shutdown_channel",
                                params=[{"channel_id":chn_id,
                                         "close_script": {
                                             "code_hash": "0x2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a",
                                             "hash_type": "data",
                                             "args": "0x0101010101010101010101010101010101010101"
                                         },
                                         "fee_rate":hex(1000)
                                         }])

    def graph_nodes(self):
        nodes = []
        after = None
        while True:
            result = self.rpc_request("graph_nodes",
                                      params=[{"limit":hex(10),
                                               "after": after
                                               }])
            if result["code"] == "error":
                return result
            else:
                data = result['data']
                if len(data['nodes']) == 0:
                    break
                for item in data["nodes"]:
                    nodes.append(item)
                after = data['last_cursor']
        return {"code": "ok", "data": nodes}

    def new_invoice_ckb(self, amount, description, preimage=None):
        if not preimage:
            preimage = '0x' + secrets.token_hex(32)
        return self.rpc_request("new_invoice",
                                params=[{"amount": hex(int(amount * 10 ** 8)),
                                         "currency": "Fibt",
                                         "description": description,
                                         "expiry": "0xe10",
                                         "payment_preimage": preimage
                                         }])

    def get_invoice(self, payment_hash):
        return self.rpc_request("get_invoice",
                                params=[{"payment_hash": payment_hash}])

    def send_payment_pay_invoice(self, invoice):
        return self.rpc_request("send_payment",
                                params=[{"invoice": invoice}])

    def parse_invoice(self, invoice):
        return self.rpc_request("parse_invoice",
                                params=[{"invoice": invoice}])

    def get_payment(self, payment_hash):
        return self.rpc_request("get_payment",
                                params=[{"payment_hash": payment_hash}])