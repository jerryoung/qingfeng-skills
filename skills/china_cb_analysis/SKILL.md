# china-cb-analysis

中国可转债 AI 分析工具 - 通过集思录数据获取和 AI 决策分析，为用户提供可转债投资建议。

## 触发词

- 可转债分析
- 转债分析
- cb analysis
- 可转债推荐
- 转债推荐

## 入口命令

```bash
python -m skills.china_cb_analysis
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | config.yaml |
| `--output` | 输出文件路径 (JSON) | 无 |
| `--filter-strict` | 使用更严格的过滤条件 | false |
| `--top-n` | 推荐标的数量 | 10 |

## 示例

```bash
# 运行完整分析
python -m skills.china_cb_analysis

# 指定输出文件
python -m skills.china_cb_analysis --output report/cb_analysis.json

# 使用严格过滤条件
python -m skills.china_cb_analysis --filter-strict

# 推荐 5 只标的
python -m skills.china_cb_analysis --top-n 5
```

## 依赖

- akshare
- pandas
- openai
- pyyaml

安装：`pip install -r requirements.txt`

## 配置

需要在 `config.yaml` 中配置：
- `jsl_cookie`: 集思录 Cookie
- `ai.api_key`: AI API 密钥
- `ai.base_url`: AI API 基础 URL
- `ai.model`: AI 模型名称
