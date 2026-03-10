#!/usr/bin/env python3
"""
配置检查脚本 - 验证 china-cb-analysis 技能的配置是否正确

使用方法:
    python scripts/check_config.py [--config PATH]

注意：AI 配置不再需要，使用 MCP AI 工具自动处理
"""

import os
import sys
import yaml
from pathlib import Path


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        # 默认使用 skill 目录下的 config.yaml
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config.yaml"
        )

    if not os.path.exists(config_path):
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_cookie(cookie: str) -> tuple:
    """检查 Cookie 是否有效"""
    if not cookie:
        return False, "Cookie 为空"
    if len(cookie) < 20:
        return False, "Cookie 格式可能不正确（太短）"
    return True, "Cookie 格式正确"


def check_filter_config(filter_config: dict) -> tuple:
    """检查过滤配置"""
    if not filter_config:
        return True, "使用默认过滤配置"

    defaults = {
        "max_price": (0, 500),
        "max_premium_ratio": (0, 100),
        "max_remaining_size": (0, 500)
    }

    warnings = []
    for key, (min_val, max_val) in defaults.items():
        if key in filter_config:
            val = filter_config[key]
            if val < min_val or val > max_val:
                warnings.append(f"{key} 超出合理范围 ({min_val}-{max_val})")

    if warnings:
        return True, "警告：" + "; ".join(warnings)
    return True, "过滤配置正确"


def main():
    """主函数"""
    print("=" * 60)
    print("中国可转债 AI 分析 - 配置检查工具")
    print("=" * 60)
    print()

    # 加载配置
    config = load_config()

    if config is None:
        print("❌ 配置文件不存在")
        print()
        print("请在以下位置创建 config.yaml 文件:")
        print(f"  {os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')}")
        print()
        print("配置模板:")
        print("""
jsl_cookie: "your_jisilu_cookie_here"

filter:
  max_price: 150
  max_premium_ratio: 50
  max_remaining_size: 50
""")
        sys.exit(1)

    print("✓ 配置文件加载成功")
    print()

    # 检查各项配置
    all_valid = True

    # 1. 检查 Cookie
    print("[1] 集思录 Cookie")
    cookie = config.get("jsl_cookie", "")
    valid, msg = check_cookie(cookie)
    if valid:
        print(f"    ✓ {msg}")
    else:
        print(f"    ❌ {msg}")
        all_valid = False
    print()

    # 2. 检查过滤配置
    print("[2] 过滤配置")
    filter_config = config.get("filter", {})
    valid, msg = check_filter_config(filter_config)
    if valid:
        if "警告" in msg:
            print(f"    ⚠️ {msg}")
        else:
            print(f"    ✓ {msg}")
        print(f"    - 最高价格：{filter_config.get('max_price', 150)} 元")
        print(f"    - 最高溢价率：{filter_config.get('max_premium_ratio', 50)}%")
        print(f"    - 最大规模：{filter_config.get('max_remaining_size', 50)} 亿")
    else:
        print(f"    ❌ {msg}")
        all_valid = False
    print()

    # 3. 检查自定义策略提示词
    strategy_prompt = config.get("ai_strategy_prompt", "")
    if strategy_prompt:
        print("[4] 自定义策略提示词")
        print(f"    ✓ 已配置 ({len(strategy_prompt)} 字符)")
        print()

    # 总结
    print("=" * 60)
    if all_valid:
        print("✓ 所有配置检查通过，可以开始使用!")
        print()
        print("运行分析:")
        print("  python -m skills.china_cb_analysis")
        print()
        print("严格模式:")
        print("  python -m skills.china_cb_analysis --filter-strict")
    else:
        print("❌ 配置检查未通过，请修正后重试")
        sys.exit(1)


if __name__ == "__main__":
    main()
