"""
数据获取模块

负责从集思录获取可转债相关数据
"""

import akshare as ak
import pandas as pd
from typing import Optional


def get_cb_index() -> pd.DataFrame:
    """
    获取可转债等权指数数据

    Returns:
        DataFrame: 包含指数代码、指数名称、开盘价、最高价、最低价、收盘价等
    """
    try:
        bond_cb_index_jsl_df = ak.bond_cb_index_jsl()
        return bond_cb_index_jsl_df
    except Exception as e:
        print(f"获取可转债等权指数失败：{e}")
        return pd.DataFrame()


def get_cb_realtime_data(cookie: str) -> pd.DataFrame:
    """
    获取可转债实时数据 (集思录)

    Args:
        cookie: 集思录 Cookie

    Returns:
        DataFrame: 包含转债代码、转债名称、正股代码、正股名称、价格、
                   涨幅、转股溢价率、余额、正股涨幅等
    """
    try:
        bond_cb_jsl_df = ak.bond_cb_jsl(cookie=cookie)
        return bond_cb_jsl_df
    except Exception as e:
        print(f"获取可转债实时数据失败：{e}")
        return pd.DataFrame()


def get_cb_redeem_data() -> pd.DataFrame:
    """
    获取可转债强赎数据

    Returns:
        DataFrame: 包含转债代码、转债名称、强赎状态、强赎日期等
    """
    try:
        bond_cb_redeem_jsl_df = ak.bond_cb_redeem_jsl()
        return bond_cb_redeem_jsl_df
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
    try:
        bond_convert_adj_logs_jsl_df = ak.bond_cb_adj_logs_jsl(symbol=symbol)
        return bond_convert_adj_logs_jsl_df
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
    try:
        # 获取基本信息
        bond_info = ak.bond_info_em(bond=code)
        return bond_info
    except Exception as e:
        print(f"获取转债详细信息失败 (code={code}): {e}")
        return None
