"""
AI 决策分析模块

调用 AI API 对候选转债进行分析和决策
"""

import json
from typing import Dict, Any, List, Optional
from openai import OpenAI


class AIAnalyzer:
    """AI 分析器"""

    def __init__(self, api_key: str, base_url: str, model: str, strategy_prompt: str = ""):
        """
        初始化 AI 分析器

        Args:
            api_key: API Key
            base_url: API Base URL
            model: 模型名称
            strategy_prompt: 策略提示词
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.strategy_prompt = strategy_prompt or self._get_default_strategy_prompt()

    def _get_default_strategy_prompt(self) -> str:
        """获取默认策略提示词"""
        return """你是一位专业的可转债投资分析师，擅长"三低优化策略"：
- 低价：关注转债价格较低，具有安全边际的标的
- 低溢价：关注转股溢价率较低，股性较强的标的
- 低余额：关注剩余规模较小，弹性较大的标的

请根据提供的数据，分析并推荐最具投资价值的可转债标的。"""

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

        # 构建提示词
        prompt = self._build_prompt(market_index, candidates_text, top_n)

        # 调用 AI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.strategy_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 分析失败：{e}"

    def _format_candidates(self, candidates: List[Dict[str, Any]]) -> str:
        """格式化候选标的信息"""
        lines = []
        for i, c in enumerate(candidates, 1):
            line = f"{i}. {c.get('代码', '')} {c.get('转债名称', '')} | "
            line += f"价格：{c.get('现价', 'N/A')} | "
            line += f"溢价率：{c.get('转股溢价率', 'N/A')}% | "
            line += f"余额：{c.get('剩余规模', 'N/A')} 亿 | "
            line += f"正股：{c.get('正股名称', 'N/A')} ({c.get('正股涨跌', 'N/A')}%)"
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
