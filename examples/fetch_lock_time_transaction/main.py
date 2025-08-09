from datetime import time
from time import sleep

import requests

def fetch_block_hash():
    """从mempool.space API获取最新区块的哈希值"""
    url = "https://mempool.space/testnet/api/blocks"
    try:
        response = requests.get(url)
        response.raise_for_status()
        blocks = response.json()
        if blocks:
            return blocks[0]['id']  # 最新区块的哈希
    except Exception as e:
        print(f"获取最新区块失败: {e}")
    return None

def fetch_block_detail(block_hash):
    """获取区块详情（包含交易总数）"""
    url = f"https://mempool.space/testnet/api/block/{block_hash}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取区块详情失败: {e}")
    return None
def fetch_block_transactions(block_hash):
    """分页获取区块中的所有交易"""
    # 先获取区块详情以确定交易总数
    block_detail = fetch_block_detail(block_hash)
    if not block_detail:
        return []

    total_txs = block_detail.get('tx_count', 0)
    print(f"区块 {block_hash} 共有 {total_txs} 笔交易")

    all_transactions = []
    start_index = 0
    page_size = 25  # API默认每次返回25笔交易

    while start_index < total_txs:
        url = f"https://mempool.space/testnet/api/block/{block_hash}/txs"
        if start_index > 0:
            url += f"/{start_index}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            transactions = response.json()

            if not transactions:
                break

            all_transactions.extend(transactions)
            fetched = len(transactions)
            start_index += fetched

            print(f"已获取 {start_index}/{total_txs} 笔交易")

            # 如果返回数量不足页面大小，说明已到最后一页
            if fetched < page_size:
                break

            # 添加延迟避免触发API限流
            sleep(0.1)

        except Exception as e:
            print(f"获取交易失败: {e}")
            break

    return all_transactions


def contains_op_checklocktimeverify(script):
    """检查脚本中是否包含OP_CHECKLOCKTIMEVERIFY (0xB1)"""
    return "OP_CHECKLOCKTIMEVERIFY" in script


def get_cltv_transactions(transactions):
    """筛选包含OP_CHECKLOCKTIMEVERIFY的交易"""
    cltv_txs = []

    for tx in transactions:
        # 检查所有输出脚本
        for vout in tx.get('vout', []):
            scriptpubkey_asm = vout.get('scriptpubkey_asm', '')
            if scriptpubkey_asm and contains_op_checklocktimeverify(scriptpubkey_asm):
                cltv_txs.append({
                    "tx_id": tx['txid'],
                    "locktime": tx.get('locktime', 0)
                })
                break  # 找到一个包含CLTV的输出即可

    return cltv_txs


def get_latest_block_cltv_txs():
    """获取最新区块中包含OP_CHECKLOCKTIMEVERIFY的交易"""
    block_hash = fetch_block_hash()
    if not block_hash:
        print("无法获取最新区块哈希")
        return []

    transactions = fetch_block_transactions(block_hash)
    print(f"成功获取 {len(transactions)} 笔交易")

    # 筛选包含OP_CHECKLOCKTIMEVERIFY的交易
    cltv_txs = get_cltv_transactions(transactions)
    print(f"找到 {len(cltv_txs)} 笔包含OP_CHECKLOCKTIMEVERIFY的交易")

    # 按交易locktime升序排序
    cltv_txs.sort(key=lambda x: x['locktime'])

    # 提取排序后的tx_id列表
    return [tx['tx_id'] for tx in cltv_txs]

# 示例用法
if __name__ == "__main__":
    tx_ids = get_latest_block_cltv_txs()
    print("\n包含OP_CHECKLOCKTIMEVERIFY的交易ID (按交易locktime升序):")
    for tx_id in tx_ids:
        print(tx_id)