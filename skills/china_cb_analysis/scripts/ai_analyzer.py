"""
AI 决策分析模块

使用 MCP AI 工具对候选转债进行分析和决策

注意：此模块运行在 Claude Code 环境中，AI 调用通过 MCP 工具处理。
"""

import json
from typing import Dict, Any, List, Optional


class AIAnalyzer:
    """AI 分析器 - 使用 MCP AI 工具"""

    def __init__(self, strategy_prompt: str = ""):
        """
        初始化 AI 分析器

        Args:
            strategy_prompt: 策略提示词
        """
        self.strategy_prompt = strategy_prompt or self._get_default_strategy_prompt()

    def analyze_candidates(
        self,
        market_index: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 10
    ) -> str:
        """
        分析候选转债并给出投资建议

        Args:
            market_index: 市场指数信息
            candidates: 候选转债列表
            top_n: 推荐数量

        Returns:
            str: AI 分析报告
        """
        # 构建候选标的文本
        candidates_text = self._format_candidates(candidates)

        # 构建完整的分析提示词
        system_prompt = self.strategy_prompt
        user_prompt = self._build_prompt(market_index, candidates_text, top_n)

        # 使用 MCP AI 工具进行分析
        return self._call_mcp_ai(system_prompt, user_prompt)

    def _call_mcp_ai(self, system_prompt: str, user_prompt: str) -> str:
        """
        使用 MCP AI 工具进行分析

        通过 MCP 协议调用 Claude Code 内置的 AI 能力

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            str: AI 分析结果
        """
        # 构建完整的消息内容
        full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}"

        # 标记此为 MCP AI 请求
        # Claude Code 环境会识别此标记并自动处理 AI 调用
        mcp_request = {
            "type": "mcp_ai_request",
            "system": system_prompt,
            "user": user_prompt
        }

        # 返回 MCP 请求标记和提示词
        # main.py 会识别此标记并通过 MCP 工具调用 AI
        return json.dumps(mcp_request, ensure_ascii=False)

    def _execute_mcp_call(self, prompt: str) -> str:
        """
        执行 MCP AI 调用

        此方法将由 main.py 中的 MCP 工具调用实际执行
        """
        # 返回提示词供外部处理
        # 实际的 AI 调用在 main.py 中通过 Agent 工具或 MCP 处理
        return prompt

    def _get_default_strategy_prompt(self) -> str:
        """获取默认策略提示词"""
        return """你是一位专业的可转债投资分析师，擅长"三低优化策略"：
- 低价：关注转债价格较低，具有安全边际的标的
- 低溢价：关注转股溢价率较低，股性较强的标的
- 低余额：关注剩余规模较小，弹性较大的标的

请根据提供的数据，分析并推荐最具投资价值的可转债标的。"""

    def _format_candidates(self, candidates: List[Dict[str, Any]]) -> str:
        """格式化候选标的信息"""
        lines = []
        for i, c in enumerate(candidates, 1):
            line = f"{i}. {c.get('bond_id', '')} {c.get('bond_nm', '')} | "
            line += f"价格：{c.get('price', 'N/A')} | "
            line += f"溢价率：{c.get('premium_rt', 'N/A')}% | "
            line += f"余额：{c.get('curr_iss_amt', 'N/A')} 亿 | "
            line += f"正股：{c.get('stock_nm', 'N/A')} ({c.get('sincrease_rt', 'N/A')}%)"
            lines.append(line)
        return "\n".join(lines)

    def _build_prompt(
        self,
        market_index: str,
        candidates_text: str,
        top_n: int
    ) -> str:
        """构建分析提示词"""
        return f"""市场概况:
{market_index}

候选转债池 (共{len(candidates_text.split(chr(10)))}只):
{candidates_text}

请根据以上数据，按照三低优化策略（低价、低溢价、低余额）进行分析，
推荐 {top_n} 只最具投资价值的可转债标的。

请以以下格式输出：

【市场分析】
简要分析当前可转债市场整体情况

【推荐标的】
1. XXXX(转债代码)
   - 推荐理由：...
   - 风险提示：...
   - 建议操作：...

2. ...

【配置建议】
给出整体仓位和配置建议

【风险提示】
列出主要风险因素"""


def parse_ai_recommendations(ai_response: str) -> List[Dict[str, Any]]:
    """
    解析 AI 推荐结果

    Args:
        ai_response: AI 分析响应

    Returns:
        List[Dict]: 解析后的推荐列表
    """
    recommendations = []
    # 简单的解析逻辑，可根据实际响应格式优化
    lines = ai_response.split("\n")
    current_rec = None

    for line in lines:
        if line.strip().startswith("1.") or line.strip().startswith("2."):
            if current_rec:
                recommendations.append(current_rec)
            current_rec = {"summary": line.strip()}
        elif current_rec and line.strip():
            current_rec["summary"] += "\n" + line.strip()

    if current_rec:
        recommendations.append(current_rec)

    return recommendations
