import requests
import hashlib
import json
from bit import Key
from bit.network.meta import Unspent

import testnet3_config
from bitcoinlib.transactions import Transaction, Input

# 配置 - 请替换以下值
SENDER_ADDRESS = testnet3_config.config['sender_address']  # 发送方比特币地址（主网）
RECEIVER_ADDRESS = testnet3_config.config['receiver_address']  # 接收方比特币地址（主网）
PRIVATE_KEY = testnet3_config.config['private_key']  # 发送方的WIF格式私钥（测试网用testnet，主网用mainnet）
AMOUNT_TO_SEND = testnet3_config.config['amount_to_send']  # 要发送的BTC数量
FEE = testnet3_config.config['fee']  # 交易费


# 获取UTXO（未花费的交易输出）
def fetch_utxos(address):
    """从mempool.space API获取UTXO"""
    url = f"https://mempool.space/testnet/api/address/{address}/utxo"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取UTXO失败: {str(e)}")
        return []


# 收集UTXO
def select_utxo(amount, fee, utxos):
    amount_sat = int(amount * 100000000)
    # 选择逻辑不变但返回整个UTXO列表
    total_needed = amount_sat + fee
    selected_utxos = []
    total_value = 0

    for utxo in sorted(utxos, key=lambda x: x['value'], reverse=True):
        if utxo.get('status', {}).get('confirmed', False):
            selected_utxos.append(utxo)
            total_value += utxo['value']
            if total_value >= total_needed:
                break

    if not selected_utxos:
        raise ValueError("没有找到已确认的UTXO")
    if total_value < total_needed:
        raise ValueError("UTXO余额不足以支付发送金额和交易费")

    return selected_utxos, amount_sat, total_value


# 广播交易
def broadcast_transaction(signed_tx_hex):
    """广播交易到比特币网络"""
    url = "https://mempool.space/testnet/api/tx"
    headers = {"Content-Type": "text/plain"}
    try:
        response = requests.post(url, data=signed_tx_hex, headers=headers)
        if response.status_code == 200:
            return response.text.strip()  # 返回交易ID
        else:
            raise Exception(f"广播失败: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"广播交易时出错: {str(e)}")


# 主程序
def main():
    print("比特币交易创建流程开始...")

    # 步骤1: 获取UTXO
    print("\n步骤1: 获取发送地址的UTXO...")
    utxos = fetch_utxos(SENDER_ADDRESS)
    if not utxos:
        print("未找到UTXO。请确认地址正确且有余额。")
        return

    print(f"找到 {len(utxos)} 个UTXO")
    print(json.dumps(utxos[0], indent=2))  # 显示第一个UTXO

    # 步骤2: 手机UTXO
    selected_utxos, amount_sat, total_input = select_utxo(
        AMOUNT_TO_SEND,
        FEE,
        utxos
    )

    # 步骤3: 创建交易
    print("\n步骤2: 创建交易结构...")
    try:
        tx = Transaction(network='testnet', fee=FEE, witness_type="legacy")
        for utxo in selected_utxos:
            tx.add_input(prev_txid=utxo['txid'], output_n=utxo['vout'], value=utxo['value'])
        tx.add_output(value=amount_sat, address=RECEIVER_ADDRESS, )
        change = total_input - amount_sat - FEE
        if change > 0:
            tx.add_output(value=change, address=SENDER_ADDRESS)
        print("交易创建成功")
    except ValueError as e:
        print(f"创建交易失败: {str(e)}")
        return

    # 步骤4: 签名交易
    print("\n步骤3: 签名交易...")
    try:
        tx.sign(keys=[PRIVATE_KEY])
        signed_tx_hex = tx.raw_hex()
        print("交易签名成功:")
        print(signed_tx_hex)
    except Exception as e:
        print(f"签名交易失败: {str(e)}")
        return

    # 步骤5: 广播交易
    print("\n步骤4: 广播交易到比特币网络...")
    try:
        txid = broadcast_transaction(signed_tx_hex)
        print(f"交易广播成功! TXID: {txid}")
        print(f"你可以在区块浏览器中查看: https://mempool.space/testnet/tx/{txid}")
    except Exception as e:
        print(f"广播交易失败: {str(e)}")


if __name__ == "__main__":
    main()
