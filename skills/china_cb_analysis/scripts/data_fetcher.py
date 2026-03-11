"""
数据获取模块

直接调用集思录 API 获取可转债数据，返回原始英文字段名
"""

import json
import time
from typing import Optional

import pandas as pd
import requests


def get_cb_index() -> pd.DataFrame:
    """
    获取可转债等权指数数据

    Returns:
        DataFrame: 包含指数历史数据
    """
    url = "https://www.jisilu.cn/webapi/cb/index_history/"
    try:
        r = requests.get(url)
        data_dict = json.loads(r.text)["data"]
        return pd.DataFrame(data_dict)
    except Exception as e:
        print(f"获取可转债等权指数失败：{e}")
        return pd.DataFrame()


def get_cb_realtime_data(cookie: str) -> pd.DataFrame:
    """
    获取可转债实时数据 (集思录)

    Args:
        cookie: 集思录 Cookie

    Returns:
        DataFrame: 包含可转债实时数据，使用原始英文字段名
    """
    url = "https://www.jisilu.cn/data/cbnew/cb_list_new/"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "content-length": "220",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": cookie,
        "origin": "https://www.jisilu.cn",
        "pragma": "no-cache",
        "referer": "https://www.jisilu.cn/data/cbnew/",
        "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.164 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    params = {
        "___jsl": f"LST___t={int(time.time() * 1000)}",
    }
    payload = {
        "fprice": "",
        "tprice": "",
        "curr_iss_amt": "",
        "volume": "",
        "svolume": "",
        "premium_rt": "",
        "ytm_rt": "",
        "market": "",
        "rating_cd": "",
        "is_search": "N",
        "market_cd[]": "shmb",
        "market_cd[]": "shkc",
        "market_cd[]": "szmb",
        "market_cd[]": "szcy",
        "btype": "",
        "listed": "Y",
        "qflag": "N",
        "sw_cd": "",
        "bond_ids": "",
        "rp": "500",
    }

    try:
        r = requests.post(url, params=params, json=payload, headers=headers)
        data_json = r.json()
        temp_df = pd.DataFrame([item["cell"] for item in data_json["rows"]])
        # 返回原始英文字段名，不做中文转换
        return temp_df
    except Exception as e:
        print(f"获取可转债实时数据失败：{e}")
        return pd.DataFrame()


def get_cb_redeem_data() -> pd.DataFrame:
    """
    获取可转债强赎数据

    Returns:
        DataFrame: 包含可转债强赎数据，使用原始英文字段名
    """
    url = "https://www.jisilu.cn/data/cbnew/redeem_list/"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "www.jisilu.cn",
        "Origin": "https://www.jisilu.cn",
        "Pragma": "no-cache",
        "Referer": "https://www.jisilu.cn/data/cbnew/",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/101.0.4951.67 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    params = {
        "___jsl": "LST___t=1653394005966",
    }
    payload = {
        "rp": "500",
    }

    try:
        r = requests.post(url, params=params, json=payload, headers=headers)
        data_json = r.json()
        temp_df = pd.DataFrame([item["cell"] for item in data_json["rows"]])
        # 返回原始英文字段名，不做中文转换
        return temp_df
    except Exception as e:
        print(f"获取可转债强赎数据失败：{e}")
        return pd.DataFrame()


def get_cb_adjustment_logs(symbol: str) -> pd.DataFrame:
    """
    获取可转债转股价格调整记录

    Args:
        symbol: 转债代码，如 "128013"

    Returns:
        DataFrame: 包含调整日期、调整前转股价、调整后转股价、调整幅度等
    """
    url = f"https://www.jisilu.cn/data/cbnew/adj_list/{symbol}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Referer": "https://www.jisilu.cn/data/cbnew/",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        r = requests.get(url, headers=headers)
        data_json = r.json()
        if data_json.get("data"):
            return pd.DataFrame(data_json["data"])
        return pd.DataFrame()
    except Exception as e:
        print(f"获取转股价格调整记录失败 (symbol={symbol}): {e}")
        return pd.DataFrame()


def get_cb_info_by_code(code: str) -> Optional[dict]:
    """
    获取单个转债的详细信息

    Args:
        code: 转债代码

    Returns:
        dict: 转债详细信息
    """
    # TODO: 实现直接调用集思录 API 获取转债详细信息
    print(f"获取转债详细信息 (code={code}): 功能待实现")
    return None