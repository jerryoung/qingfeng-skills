"""
数据过滤模块

根据预设条件过滤候选转债标的
"""

import pandas as pd
from typing import Dict, Any


def filter_cb_data(
    cb_data: pd.DataFrame,
    redeem_codes: set = None,
    config: Dict[str, Any] = None
) -> pd.DataFrame:
    """
    根据配置条件过滤可转债数据

    Args:
        cb_data: 可转债实时数据 DataFrame
        redeem_codes: 已公告强赎的转债代码集合
        config: 过滤配置

    Returns:
        DataFrame: 过滤后的候选转债数据
    """
    if config is None:
        config = {
            "max_remaining_size": 50,
            "max_price": 150,
            "max_premium_ratio": 50,
            "exclude_st": True,
            "exclude_redeem": True,
        }

    if redeem_codes is None:
        redeem_codes = set()

    filtered = cb_data.copy()

    # 1. 排除已公告强赎的转债
    if config.get("exclude_redeem", True) and redeem_codes:
        filtered = filtered[~filtered["转债代码"].isin(redeem_codes)]
        print(f"排除 {len(redeem_codes)} 只已公告强赎的转债")

    # 2. 排除剩余规模过大的转债
    max_size = config.get("max_remaining_size", 50)
    if "剩余规模" in filtered.columns:
        filtered = filtered[filtered["剩余规模"] <= max_size]
        print(f"排除剩余规模 > {max_size} 亿的转债")

    # 3. 排除价格过高的转债
    max_price = config.get("max_price", 150)
    if "现价" in filtered.columns:
        filtered = filtered[filtered["现价"] <= max_price]
        print(f"排除价格 > {max_price} 元的转债")

    # 4. 排除溢价率过高的转债
    max_premium = config.get("max_premium_ratio", 50)
    if "转股溢价率" in filtered.columns:
        filtered = filtered[filtered["转股溢价率"] <= max_premium]
        print(f"排除转股溢价率 > {max_premium}% 的转债")

    # 5. 排除正股 ST 的转债
    if config.get("exclude_st", True):
        if "正股名称" in filtered.columns:
            filtered = filtered[~filtered["正股名称"].str.contains("ST", case=False, na=False)]
            print("排除正股 ST 的转债")

    print(f"\n过滤后候选标的数量：{len(filtered)}")
    return filtered


def get_filter_stats(original_data: pd.DataFrame, filtered_data: pd.DataFrame) -> Dict[str, Any]:
    """
    获取过滤统计信息

    Args:
        original_data: 原始数据
        filtered_data: 过滤后的数据

    Returns:
        dict: 过滤统计信息
    """
    return {
        "original_count": len(original_data),
        "filtered_count": len(filtered_data),
        "removed_count": len(original_data) - len(filtered_data),
        "filter_rate": f"{(1 - len(filtered_data) / len(original_data)) * 100:.1f}%" if len(original_data) > 0 else "0%",
    }
