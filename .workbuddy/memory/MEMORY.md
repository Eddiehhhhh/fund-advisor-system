# 基金理财顾问系统

## 系统信息
- 位置: /Users/eddie/WorkBuddy/20260411044453/fund_advisor_system
- 配置文件: config.yaml
- 主程序: main.py
- 报告目录: data/reports/

## 已配置基金池 (19只)
- 宽基: 沪深300、中证500、创业板指、科创50、上证50、中证1000
- 行业: 白酒、医疗、新能源、半导体、军工、银行、证券公司、房地产、人工智能、传媒
- 海外: 纳斯达克100、标普500、恒生指数

## 环境信息 (2026-04-11更新)
- Python虚拟环境: /Users/eddie/.workbuddy/binaries/python/envs/default (Python 3.13.12)
- akshare版本: 1.18.54
- 估值数据API: stock_zh_index_value_csindex (已修复兼容性)
- 部分指数(399006/NDX/SPX/HSI)估值API返回404，需备用数据源

## 待改进
- main.py中technical/fundamental/sentiment数据为硬编码相同值，导致评分差异化不足
- 北向资金数据获取失败返回nan
- 399006(创业板指)、海外指数(NDX/SPX/HSI)需要备用估值数据源
- 邮件发送失败: SMTP配置未完成，需配置真实的邮箱授权码
- 企业微信/飞书/钉钉: 未启用

## 推送配置状态
- 邮件: 已配置但未完成授权码设置
- 企业微信/飞书/钉钉: 未启用
