import requests


def get_transaction_details(txid, testnet=False):
    """
    通过 mempool.space API 查询比特币交易详情

    参数:
    txid (str): 比特币交易ID
    testnet (bool): 是否使用测试网络 (默认: False 主网)

    返回:
    dict: 交易详情的JSON数据，或包含错误信息的字典
    """
    # 设置API端点 (主网或测试网)
    base_url = "https://mempool.space/testnet/api" if testnet else "https://mempool.space/api"
    url = f"{base_url}/tx/{txid}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查HTTP错误状态
        return response.json()  # 返回解析后的JSON数据
    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败: {str(e)}"}
    except ValueError as e:
        return {"error": f"JSON解析失败: {str(e)}"}


# 示例用法
if __name__ == "__main__":
    # 替换为你要查询的交易ID（测试网示例）
    txid = "3e0140ba728c64b04de9746fe79d6df26cb1c9a135a872bd41d3cec6453da899"

    # 查询交易详情 (主网)
    details = get_transaction_details(txid, True)

    if "error" in details:
        print(f"错误: {details['error']}")
    else:
        # 打印部分关键信息
        print(f"交易ID: {details['txid']}")
        print(f"区块高度: {details.get('status', {}).get('block_height', '未确认')}")
        print(f"输入数量: {len(details.get('vin', []))}")
        print(f"输出数量: {len(details.get('vout', []))}")
        print(f"交易大小: {details['size']} 字节")
        print(f"手续费: {details['fee']} satoshis")

        # 打印输出详情
        print("\n输出详情:")
        for output in details['vout']:
            print(f"→ {output['value']} satoshis 到 {output['scriptpubkey_address']}")
