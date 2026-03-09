"""
可转债 AI 分析主程序

工作流:
1. 加载配置
2. 获取市场数据 (指数 + 实时数据 + 强赎数据)
3. 执行固定条件过滤，生成候选池
4. AI 分析候选标的
5. 输出最终推荐列表和分析报告
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import yaml

from .scripts import data_fetcher
from .scripts import data_filter
from .scripts import ai_analyzer


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认按以下顺序查找：
                     1. 指定的 config_path
                     2. 当前目录下的 config.yaml
                     3. 当前目录下的 config.yaml.local

    Returns:
        Dict: 配置字典
    """
    if config_path is None:
        base_dir = os.path.dirname(__file__)
        # 优先使用 config.yaml（本地配置，应在 .gitignore 中）
        config_path = os.path.join(base_dir, "config.yaml")
        if not os.path.exists(config_path):
            # 回退到 config.yaml.local
            config_path = os.path.join(base_dir, "config.yaml.local")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"配置文件不存在：{config_path}\n"
            f"请复制 config.example.yaml 并填写配置"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_market_index(index_df: pd.DataFrame) -> str:
    """格式化市场指数信息"""
    if index_df.empty:
        return "市场指数数据获取失败"

    # 取最新数据
    latest = index_df.iloc[-1] if len(index_df) > 0 else None
    if latest is None:
        return "市场指数数据获取失败"

    return f"""
- 指数点位：{latest.get('idx_price', 'N/A')}
- 涨跌幅：{latest.get('idx_increase_rt', 'N/A')}%
- 均价：{latest.get('price', 'N/A')}
- 中位数价格：{latest.get('mid_price', 'N/A')}
- 平均溢价率：{latest.get('avg_premium_rt', 'N/A')}%
- 中位数溢价率：{latest.get('mid_premium_rt', 'N/A')}%
- 市场温度：{latest.get('temperature', 'N/A')}
"""


def run_analysis(
    config_path: Optional[str] = None,
    output_path: Optional[str] = None,
    filter_strict: bool = False,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    执行可转债 AI 分析

    Args:
        config_path: 配置文件路径
        output_path: 输出文件路径
        filter_strict: 是否使用更严格的过滤条件
        top_n: 推荐标的数量

    Returns:
        Dict: 分析结果
    """
    print("=" * 60)
    print("中国可转债 AI 分析工具")
    print("=" * 60)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 加载配置
    print("[1/5] 加载配置文件...")
    config = load_config(config_path)

    jsl_cookie = config.get("jsl_cookie", "")
    if not jsl_cookie:
        raise ValueError("请配置集思录 Cookie (jsl_cookie)")

    ai_config = config.get("ai", {})
    if not ai_config.get("api_key"):
        raise ValueError("请配置 AI API Key")

    filter_config = config.get("filter", {})

    # 严格模式：调整过滤参数
    if filter_strict:
        filter_config["max_price"] = 120
        filter_config["max_premium_ratio"] = 30
        filter_config["max_remaining_size"] = 30
        print("使用严格过滤模式")

    # 2. 获取市场数据
    print("\n[2/5] 获取市场数据...")

    # 获取指数数据
    print("  - 获取可转债等权指数...")
    index_df = data_fetcher.get_cb_index()

    # 获取实时数据
    print("  - 获取可转债实时数据...")
    cb_data = data_fetcher.get_cb_realtime_data(cookie=jsl_cookie)

    # 获取强赎数据
    print("  - 获取强赎数据...")
    redeem_df = data_fetcher.get_cb_redeem_data()
    # 过滤所有强赎相关的转债（包括已公告、公告要强赎、已满足条件等）
    if not redeem_df.empty and "强赎状态" in redeem_df.columns:
        # 只过滤有强赎风险的转债（不包括空值和"公告不强赎"）
        redeem_status_df = redeem_df[
            redeem_df["强赎状态"].isin(["已公告强赎", "公告要强赎", "已满足强赎条件"])
        ]
        redeem_codes = set(redeem_status_df["代码"].tolist())
    else:
        redeem_codes = set()

    print(f"\n  市场数据获取完成:")
    print(f"  - 可转债总数：{len(cb_data)}")
    print(f"  - 已公告强赎：{len(redeem_codes)}")

    # 3. 执行过滤
    print("\n[3/5] 执行条件过滤...")
    filtered_data = data_filter.filter_cb_data(
        cb_data=cb_data,
        redeem_codes=redeem_codes,
        config=filter_config
    )

    filter_stats = data_filter.get_filter_stats(cb_data, filtered_data)
    print(f"  - 过滤前：{filter_stats['original_count']} 只")
    print(f"  - 过滤后：{filter_stats['filtered_count']} 只")
    print(f"  - 过滤率：{filter_stats['filter_rate']}")

    if filtered_data.empty:
        print("\n警告：过滤后无候选标的，请调整过滤条件")
        return {"error": "No candidates after filtering"}

    # 4. AI 分析
    print("\n[4/5] AI 分析候选标的...")
    analyzer = ai_analyzer.AIAnalyzer(
        api_key=ai_config["api_key"],
        base_url=ai_config["base_url"],
        model=ai_config["model"],
        strategy_prompt=config.get("ai_strategy_prompt", "")
    )

    # 格式化市场指数
    market_index_text = format_market_index(index_df)

    # 转换候选数据为字典列表
    candidates = filtered_data.to_dict("records")

    # AI 分析
    print(f"  - 分析 {len(candidates)} 只候选转债...")
    ai_response = analyzer.analyze_candidates(
        market_index=market_index_text,
        candidates=candidates,
        top_n=top_n
    )

    # 5. 输出结果
    print("\n[5/5] 输出分析结果...")
    print("\n" + "=" * 60)
    print("AI 分析报告")
    print("=" * 60)
    print(ai_response)
    print("=" * 60)

    # 构建结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "market_stats": {
            "total_cb": len(cb_data),
            "redeem_count": len(redeem_codes),
            "candidates": len(filtered_data),
        },
        "filter_stats": filter_stats,
        "ai_analysis": ai_response,
        "candidates": candidates,
    }

    # 保存到文件
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到：{output_path}")

    # 同时保存 Markdown 格式报告
    if output_path:
        md_path = output_path.replace(".json", ".md")
        if md_path == output_path:
            md_path = output_path + ".md"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 可转债 AI 分析报告\n\n")
            f.write(f"**分析时间**: {result['timestamp']}\n\n")
            f.write(f"## 市场概况\n\n")
            f.write(f"- 可转债总数：{result['market_stats']['total_cb']}\n")
            f.write(f"- 已公告强赎：{result['market_stats']['redeem_count']}\n")
            f.write(f"- 候选标的：{result['market_stats']['candidates']}\n\n")
            f.write(f"## 过滤统计\n\n")
            f.write(f"- 过滤前：{filter_stats['original_count']} 只\n")
            f.write(f"- 过滤后：{filter_stats['filtered_count']} 只\n")
            f.write(f"- 过滤率：{filter_stats['filter_rate']}\n\n")
            f.write(f"## AI 分析\n\n")
            f.write(f"{ai_response}\n")

        print(f"Markdown 报告已保存到：{md_path}")

    return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="中国可转债 AI 分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整分析
  python -m skills.china_cb_analysis

  # 指定输出文件
  python -m skills.china_cb_analysis --output report/cb_analysis.json

  # 使用严格过滤条件
  python -m skills.china_cb_analysis --filter-strict

  # 推荐 5 只标的
  python -m skills.china_cb_analysis --top-n 5
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (默认：config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径 (JSON 格式)"
    )
    parser.add_argument(
        "--filter-strict",
        action="store_true",
        help="使用更严格的过滤条件"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="推荐标的数量 (默认：10)"
    )

    args = parser.parse_args()

    try:
        run_analysis(
            config_path=args.config,
            output_path=args.output,
            filter_strict=args.filter_strict,
            top_n=args.top_n
        )
    except Exception as e:
        print(f"\n错误：{e}")
        exit(1)


if __name__ == "__main__":
    main()
