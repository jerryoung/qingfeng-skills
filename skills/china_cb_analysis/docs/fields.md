# 集思录可转债数据字段说明

本文档记录集思录 API 返回的可转债数据字段，AI 可参考此文档理解数据含义。

## 可转债实时数据 (bond_cb_jsl)

| 字段名 | 中文含义 | 数据类型 | 说明 |
|--------|----------|----------|------|
| bond_id | 转债代码 | string | 可转债的唯一标识，如 "128013" |
| bond_nm | 转债简称 | string | 可转债的简称 |
| price | 现价 | float | 当前交易价格（元） |
| increase_rt | 涨跌幅 | float | 当日涨跌幅（%） |
| stock_id | 正股代码 | string | 对应正股的股票代码 |
| stock_nm | 正股名称 | string | 对应正股的股票名称 |
| sprice | 正股价 | float | 正股当前价格（元） |
| sincrease_rt | 正股涨跌 | float | 正股涨跌幅（%） |
| pb | 正股PB | float | 正股市净率 |
| convert_price | 转股价 | float | 转股价（元） |
| convert_value | 转股价值 | float | 转股价值 = 正股价格 / 转股价 × 100 |
| premium_rt | 转股溢价率 | float | 转股溢价率（%）= (转债价格 - 转股价值) / 转股价值 × 100 |
| dblow | 双低 | float | 双低指标 = 转债价格 + 转股溢价率 × 100 |
| rating_cd | 债券评级 | string | 债券评级，如 "AAA", "AA+", "AA" 等 |
| put_convert_price | 回售触发价 | float | 回售触发价格（元） |
| force_redeem_price | 强赎触发价 | float | 强赎触发价格（元） |
| convert_amt_ratio | 转债占比 | float | 转债占正股市值比例（%） |
| maturity_dt | 到期时间 | date | 到期日期 |
| year_left | 剩余年限 | float | 剩余到期年限 |
| curr_iss_amt | 剩余规模 | float | 剩余未转股规模（亿元） |
| volume | 成交额 | float | 当日成交额（万元） |
| turnover_rt | 换手率 | float | 当日换手率（%） |
| ytm_rt | 到期税前收益 | float | 到期税前收益率（%） |

## 强赎数据 (bond_cb_redeem_jsl)

| 字段名 | 中文含义 | 数据类型 | 说明 |
|--------|----------|----------|------|
| bond_id | 转债代码 | string | 可转债的唯一标识 |
| bond_nm | 名称 | string | 可转债简称 |
| price | 现价 | float | 当前价格 |
| stock_id | 正股代码 | string | 正股代码 |
| stock_nm | 正股名称 | string | 正股名称 |
| orig_iss_amt | 规模 | float | 发行规模（亿元） |
| curr_iss_amt | 剩余规模 | float | 剩余规模（亿元） |
| convert_dt | 转股起始日 | date | 开始转股日期 |
| convert_price | 转股价 | float | 转股价 |
| redeem_price_ratio | 强赎触发比 | float | 强赎触发比例（%） |
| real_force_redeem_price | 强赎价 | float | 实际强赎触发价格 |
| redeem_tc | 强赎条款 | string | 强赎条款描述 |
| sprice | 正股价 | float | 正股价格 |
| delist_dt | 最后交易日 | date | 最后交易日期 |
| maturity_dt | 到期日 | date | 到期日期 |
| redeem_icon | 强赎状态 | string | 强赎状态标识：<br>- 空: 无风险<br>- "G": 已公告强赎<br>- "R": 满足强赎条件<br>- "O": 其他 |
| force_redeem_price | 强赎触发价 | float | 强赎触发价格 |

## 可转债等权指数 (bond_cb_index_jsl)

| 字段名 | 中文含义 | 数据类型 | 说明 |
|--------|----------|----------|------|
| idx_price | 指数点位 | float | 可转债等权指数点位 |
| idx_increase_rt | 涨跌幅 | float | 指数涨跌幅（%） |
| price | 均价 | float | 可转债平均价格 |
| mid_price | 中位数价格 | float | 可转债价格中位数 |
| avg_premium_rt | 平均溢价率 | float | 平均转股溢价率（%） |
| mid_premium_rt | 中位数溢价率 | float | 中位数转股溢价率（%） |
| temperature | 市场温度 | float | 市场温度计指标 |

## 字段使用建议

### 过滤条件对应字段

- **价格过滤**: `price` (现价)
- **溢价率过滤**: `premium_rt` (转股溢价率)
- **规模过滤**: `curr_iss_amt` (剩余规模)
- **涨跌幅过滤**: `increase_rt` (涨跌幅)
- **成交额过滤**: `volume` (成交额，用于排除未上市)
- **ST股票排除**: `stock_nm` (正股名称，包含 "ST" 则排除)

### 推荐指标

- **双低排序**: `dblow` (双低指标，越低越好)
- **低溢价**: `premium_rt` (转股溢价率，越低越好)
- **低价格**: `price` (现价，越低越安全)
- **小规模**: `curr_iss_amt` (剩余规模，越小弹性越大)
- **高评级**: `rating_cd` (债券评级，AAA 最高)
- **高到期收益**: `ytm_rt` (到期税前收益)