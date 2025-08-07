import requests

import testnet3_config


def get_btc_balance(address):
    url = f"https://mempool.space/testnet/api/address/{address}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查HTTP错误
        data = response.json()

        # 提取链上确认的余额
        confirmed_balance = data['chain_stats']['funded_txo_sum'] - data['chain_stats']['spent_txo_sum']

        # 提取未确认交易的余额
        unconfirmed_balance = data['mempool_stats']['funded_txo_sum'] - data['mempool_stats']['spent_txo_sum']

        # 计算总余额（单位：聪）
        total_balance = confirmed_balance + unconfirmed_balance

        # 转换为BTC（可选）
        total_balance_btc = total_balance / 100000000

        return {
            "address": address,
            "confirmed": confirmed_balance,
            "unconfirmed": unconfirmed_balance,
            "total_sats": total_balance,
            "total_btc": total_balance_btc
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"网络请求失败: {str(e)}"}
    except KeyError:
        return {"error": "无效的API响应，请检查地址格式"}


# 示例用法
if __name__ == "__main__":
    address = testnet3_config.config['address']
    balance_info = get_btc_balance(address)

    if "error" in balance_info:
        print(f"错误: {balance_info['error']}")
    else:
        print(f"地址: {balance_info['address']}")
        print(f"已确认余额: {balance_info['confirmed']} satoshis")
        print(f"未确认余额: {balance_info['unconfirmed']} satoshis")
        print(f"总余额: {balance_info['total_sats']} satoshis")
        print(f"≈ {balance_info['total_btc']:.8f} BTC")
