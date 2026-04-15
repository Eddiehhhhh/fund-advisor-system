#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化报告生成器 V3 - 增强版
增加：板块分析、更多推荐基金、更详细的市场解读
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class VisualReportGeneratorV3:
    """生成增强版HTML报告"""
    
    def __init__(self):
        self.colors = {
            'up': '#e74c3c',
            'down': '#27ae60',
            'neutral': '#95a5a6',
            'primary': '#3498db',
            'warning': '#f39c12',
            'success': '#2ecc71',
            'bg': '#f5f7fa',
            'card': '#ffffff',
        }
    
    def generate_report(self, 
                       market_data: Dict,
                       portfolio_analysis: Dict,
                       opportunities: List[Dict],
                       fund_scores: List[Dict]) -> str:
        """生成完整报告"""
        
        # 准备板块数据
        sector_analysis = self._analyze_sectors(fund_scores)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金日报 - {datetime.now().strftime('%m月%d日')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: {self.colors['bg']}; 
            line-height: 1.6; 
            color: #333;
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 16px; }}
        
        /* 头部 */
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 24px 20px; 
            border-radius: 16px; 
            margin-bottom: 16px;
            text-align: center;
        }}
        .header h1 {{ font-size: 22px; margin-bottom: 6px; font-weight: 600; }}
        .header .date {{ opacity: 0.85; font-size: 13px; }}
        .header .summary {{ 
            margin-top: 12px; 
            padding-top: 12px; 
            border-top: 1px solid rgba(255,255,255,0.2);
            font-size: 14px;
        }}
        
        /* 卡片 */
        .card {{ 
            background: {self.colors['card']}; 
            border-radius: 12px; 
            padding: 20px; 
            margin-bottom: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .card-title {{ 
            font-size: 16px; 
            font-weight: 600; 
            margin-bottom: 16px; 
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        /* 市场概况 */
        .market-simple {{
            display: flex;
            justify-content: space-between;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .market-item-simple {{
            text-align: center;
            flex: 1;
        }}
        .market-item-simple .label {{
            font-size: 12px;
            color: #888;
            margin-bottom: 4px;
        }}
        .market-item-simple .value {{
            font-size: 20px;
            font-weight: 700;
        }}
        .market-item-simple .sub {{
            font-size: 12px;
            margin-top: 2px;
        }}
        
        /* 市场解读 */
        .market-insight {{
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            padding: 16px;
            border-radius: 10px;
            margin-top: 12px;
            font-size: 14px;
            color: #444;
        }}
        .market-insight strong {{
            color: #1565c0;
        }}
        
        /* 持仓总览 */
        .portfolio-big {{
            text-align: center;
            padding: 20px 0;
        }}
        .big-number {{
            font-size: 36px;
            font-weight: 700;
            color: #2c3e50;
        }}
        .big-number.positive {{ color: {self.colors['up']}; }}
        .big-number.negative {{ color: {self.colors['down']}; }}
        .big-label {{
            font-size: 13px;
            color: #888;
            margin-top: 4px;
        }}
        .portfolio-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 18px;
            font-weight: 600;
        }}
        .stat-value.positive {{ color: {self.colors['up']}; }}
        .stat-value.negative {{ color: {self.colors['down']}; }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            margin-top: 2px;
        }}
        
        /* 持仓列表 */
        .holding-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .holding-row {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 10px;
            transition: background 0.2s;
        }}
        .holding-row:hover {{ background: #f0f2f5; }}
        .holding-name {{
            flex: 1;
            font-size: 14px;
            font-weight: 500;
        }}
        .holding-amount {{
            font-size: 13px;
            color: #888;
            margin-right: 16px;
        }}
        .holding-return {{
            font-size: 15px;
            font-weight: 600;
            min-width: 70px;
            text-align: right;
        }}
        .holding-tag {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 8px;
            font-weight: 500;
        }}
        .tag-buy {{ background: #ffebee; color: #c62828; }}
        .tag-hold {{ background: #e3f2fd; color: #1565c0; }}
        .tag-watch {{ background: #fff3e0; color: #ef6c00; }}
        
        /* 行动建议 */
        .action-card {{
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 12px;
        }}
        .action-card.buy {{
            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
            border: 1px solid #ef9a9a;
        }}
        .action-card.hold {{
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border: 1px solid #90caf9;
        }}
        .action-card.watch {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border: 1px solid #ffcc80;
        }}
        .action-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .action-text {{
            font-size: 14px;
            color: #555;
            line-height: 1.6;
        }}
        .action-funds {{
            font-weight: 600;
            color: #333;
        }}
        
        /* 板块分析 */
        .sector-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        .sector-item {{
            padding: 14px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid {self.colors['primary']};
        }}
        .sector-item.hot {{ border-left-color: {self.colors['up']}; }}
        .sector-item.cold {{ border-left-color: {self.colors['down']}; }}
        .sector-name {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .sector-score {{
            font-size: 18px;
            font-weight: 700;
            color: {self.colors['primary']};
        }}
        .sector-score.high {{ color: {self.colors['up']}; }}
        .sector-score.low {{ color: {self.colors['down']}; }}
        .sector-desc {{
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }}
        
        /* 推荐基金 */
        .fund-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .fund-item {{
            padding: 16px;
            background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
            border-radius: 10px;
            border: 1px solid #e8ecf1;
        }}
        .fund-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .fund-name {{
            font-weight: 600;
            font-size: 15px;
        }}
        .fund-badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-buy {{ background: #ffebee; color: #c62828; }}
        .badge-watch {{ background: #fff3e0; color: #ef6c00; }}
        .badge-hold {{ background: #e8f5e9; color: #2e7d32; }}
        .fund-reason {{
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }}
        
        /* 交易计划卡片 */
        .trading-plan-card {{
            background: linear-gradient(135deg, #fff8e1 0%, #ffffff 100%);
            border: 1px solid #ffe082;
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
        }}
        .plan-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px dashed #ffd54f;
        }}
        .plan-title {{
            font-weight: 600;
            font-size: 14px;
            color: #f57c00;
        }}
        .position-tag {{
            font-size: 12px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .plan-content {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .plan-row {{
            display: flex;
            align-items: flex-start;
            gap: 6px;
            font-size: 13px;
        }}
        .plan-label {{
            color: #666;
            white-space: nowrap;
        }}
        .plan-value {{
            color: #333;
            font-weight: 500;
        }}
        .plan-value.highlight {{
            color: #e65100;
            font-weight: 600;
        }}
        .event-row {{
            background: #e3f2fd;
            padding: 8px;
            border-radius: 4px;
            margin-top: 4px;
        }}
        .position-desc {{
            font-size: 12px;
            color: #888;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px dashed #ffd54f;
            font-style: italic;
        }}
        
        /* 推荐理由列表 */
        .reason-list {{
            list-style: none;
            padding: 0;
            margin: 0 0 12px 0;
        }}
        .reason-item {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 8px 0;
            border-bottom: 1px dashed #eee;
            font-size: 13px;
            line-height: 1.5;
        }}
        .reason-item:last-child {{
            border-bottom: none;
        }}
        .reason-icon {{
            font-size: 14px;
            flex-shrink: 0;
            margin-top: 1px;
        }}
        .reason-text {{
            color: #555;
        }}
        .fund-metrics {{
            display: flex;
            gap: 20px;
            font-size: 12px;
        }}
        .metric {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        .metric-label {{ color: #888; }}
        .metric-value {{ font-weight: 600; }}
        
        /* 机会列表 */
        .opportunity-card {{
            padding: 16px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid {self.colors['primary']};
        }}
        .opp-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .opp-name {{
            font-weight: 600;
            font-size: 15px;
        }}
        .opp-score {{
            background: {self.colors['primary']};
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .opp-reason {{
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }}
        .opp-prices {{
            display: flex;
            gap: 24px;
            font-size: 13px;
        }}
        .opp-prices .label {{
            color: #888;
        }}
        .opp-prices .value {{
            font-weight: 600;
            color: #333;
        }}
        
        /* 图表 */
        .chart-container {{
            position: relative;
            height: 220px;
            margin: 16px 0;
        }}
        
        /* 底部 */
        .footer {{
            text-align: center;
            padding: 24px 20px;
            color: #999;
            font-size: 12px;
        }}
        
        /* 颜色 */
        .up {{ color: {self.colors['up']}; }}
        .down {{ color: {self.colors['down']}; }}
        
        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 32px 20px;
            color: #999;
        }}
        .empty-state .icon {{
            font-size: 32px;
            margin-bottom: 8px;
        }}
        
        /* 响应式 */
        @media (max-width: 600px) {{
            .market-simple {{ flex-direction: column; gap: 12px; }}
            .portfolio-stats {{ gap: 24px; }}
            .holding-row {{ flex-wrap: wrap; }}
            .holding-amount {{ width: 100%; margin: 4px 0 0 0; }}
            .sector-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📊 基金理财日报</h1>
            <div class="date">{datetime.now().strftime('%Y年%m月%d日')}</div>
            <div class="summary">{self._generate_market_summary(market_data, portfolio_analysis)}</div>
        </div>
        
        <!-- 市场概况 -->
        <div class="card">
            <div class="card-title">📈 今天市场怎么样</div>
            <div class="market-simple">
                <div class="market-item-simple">
                    <div class="label">上证指数</div>
                    <div class="value {'up' if market_data.get('sh_change', 0) >= 0 else 'down'}">{market_data.get('sh_index', 'N/A')}</div>
                    <div class="sub {'up' if market_data.get('sh_change', 0) >= 0 else 'down'}">{market_data.get('sh_change', 0):+.2f}%</div>
                </div>
                <div class="market-item-simple">
                    <div class="label">涨跌情况</div>
                    <div class="value" style="font-size: 16px;">{market_data.get('up_count', 0)}涨 {market_data.get('down_count', 0)}跌</div>
                    <div class="sub">{market_data.get('up_ratio', 0):.0f}%股票上涨</div>
                </div>
                <div class="market-item-simple">
                    <div class="label">市场情绪</div>
                    <div class="value" style="font-size: 16px;">{market_data.get('sentiment', '中性')}</div>
                    <div class="sub">恐贪指数 {market_data.get('fear_greed', 50)}</div>
                </div>
            </div>
            
            <!-- 资金流向分析 -->
            <div class="fund-flow-section" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #eee;">
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #2c3e50;">💰 资金流向</div>
                <div class="fund-flow-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    {self._generate_fund_flow_html(market_data)}
                </div>
            </div>
            
            <div class="market-insight">
                {self._generate_market_commentary(market_data)}
            </div>
        </div>
        
        <!-- 持仓总览 -->
        <div class="card">
            <div class="card-title">💰 我的持仓</div>
            <div class="portfolio-big">
                <div class="big-number">¥{portfolio_analysis.get('total_value', 0):,.0f}</div>
                <div class="big-label">总持仓</div>
                
                <div class="portfolio-stats">
                    <div class="stat-item">
                        <div class="stat-value {'positive' if portfolio_analysis.get('total_return', 0) >= 0 else 'negative'}">
                            {'+' if portfolio_analysis.get('total_return', 0) >= 0 else ''}¥{portfolio_analysis.get('total_return', 0):,.0f}
                        </div>
                        <div class="stat-label">总盈亏</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value {'positive' if portfolio_analysis.get('total_return_pct', 0) >= 0 else 'negative'}">
                            {portfolio_analysis.get('total_return_pct', 0):+.2f}%
                        </div>
                        <div class="stat-label">收益率</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 持仓明细 -->
        <div class="card">
            <div class="card-title">📋 持仓明细</div>
            <div class="holding-list">
                {self._generate_holdings_html(portfolio_analysis.get('holdings', []))}
            </div>
        </div>
        
        <!-- 今天该做什么 -->
        <div class="card">
            <div class="card-title">💡 今天该做什么</div>
            {self._generate_action_html(portfolio_analysis.get('holdings', []))}
        </div>
        
        <!-- 板块热度分析 -->
        <div class="card">
            <div class="card-title">🔥 板块热度排行</div>
            <div class="sector-grid">
                {self._generate_sector_html(sector_analysis)}
            </div>
        </div>
        
        <!-- 今日推荐基金 -->
        <div class="card">
            <div class="card-title">⭐ 今日推荐基金</div>
            <div class="fund-list">
                {self._generate_recommended_funds_html(fund_scores)}
            </div>
        </div>
        
        <!-- 持仓机会 -->
        <div class="card">
            <div class="card-title">🎯 持仓买入机会</div>
            {self._generate_opportunities_html(opportunities[:3])}
        </div>
        
        <!-- 持仓分布 -->
        <div class="card">
            <div class="card-title">📊 持仓分布</div>
            <div class="chart-container">
                <canvas id="allocationChart"></canvas>
            </div>
        </div>
        
        <!-- 底部 -->
        <div class="footer">
            <p>本报告仅供参考，不构成投资建议</p>
            <p>投资有风险，入市需谨慎</p>
        </div>
    </div>
    
    <script>
        // 持仓分布饼图
        const ctx = document.getElementById('allocationChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps([h.get('name', '未知')[:8] for h in portfolio_analysis.get('holdings', [])[:6]])},
                datasets: [{{
                    data: {json.dumps([h.get('amount', 0) for h in portfolio_analysis.get('holdings', [])[:6]])},
                    backgroundColor: [
                        '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
                        '#9b59b6', '#1abc9c'
                    ],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ boxWidth: 12, font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_market_summary(self, market_data: Dict, portfolio_analysis: Dict) -> str:
        """生成市场摘要"""
        sh_change = market_data.get('sh_change', 0)
        total_return = portfolio_analysis.get('total_return_pct', 0)
        
        if sh_change > 1:
            market_status = "市场大涨"
        elif sh_change > 0:
            market_status = "市场小涨"
        elif sh_change > -1:
            market_status = "市场微跌"
        else:
            market_status = "市场调整"
        
        if total_return > 0:
            portfolio_status = f"持仓盈利 +{total_return:.2f}%"
        else:
            portfolio_status = f"持仓亏损 {total_return:.2f}%"
        
        return f"{market_status} | {portfolio_status}"
    
    def _generate_market_commentary(self, market_data: Dict) -> str:
        """生成市场解读"""
        sh_change = market_data.get('sh_change', 0)
        up_ratio = market_data.get('up_ratio', 50)
        fear_greed = market_data.get('fear_greed', 50)
        north_flow = market_data.get('north_money_flow', 0)
        main_flow = market_data.get('main_money_flow', 0)
        vol_ratio = market_data.get('volume_ratio', 1.0)
        
        commentary = ""
        
        # 涨跌解读
        if sh_change > 1:
            commentary += "今天市场表现不错，上证指数涨超1%，整体情绪偏乐观。"
        elif sh_change > 0:
            commentary += "今天市场小幅上涨，整体走势平稳。"
        elif sh_change > -1:
            commentary += "今天市场小幅调整，属于正常波动范围。"
        else:
            commentary += "今天市场出现一定调整，建议保持观望。"
        
        # 涨跌家数解读
        if up_ratio > 60:
            commentary += "上涨股票占多数，赚钱效应较好。"
        elif up_ratio < 40:
            commentary += "下跌股票较多，需要谨慎操作。"
        else:
            commentary += "涨跌家数相对均衡，结构性行情明显。"
        
        # 资金流向解读
        commentary += "<br><br><strong>💰 资金流向分析：</strong><br>"
        
        # 北向资金
        if north_flow > 50:
            commentary += "北向资金大幅净流入，外资看好A股市场，这是个积极信号。"
        elif north_flow > 0:
            commentary += "北向资金小幅净流入，外资态度偏谨慎乐观。"
        elif north_flow > -50:
            commentary += "北向资金小幅净流出，外资在观望。"
        else:
            commentary += "北向资金大幅净流出，外资在撤退，需要警惕。"
        
        # 主力资金
        if main_flow > 100:
            commentary += "主力资金也在大幅流入，机构资金进场明显。"
        elif main_flow > 0:
            commentary += "主力资金小幅流入，机构在逐步建仓。"
        elif main_flow > -100:
            commentary += "主力资金小幅流出，机构在调仓换股。"
        else:
            commentary += "主力资金大幅流出，机构在减仓。"
        
        # 成交量
        if vol_ratio > 1.3:
            commentary += "今天成交量明显放大，市场活跃度提升。"
        elif vol_ratio < 0.7:
            commentary += "今天成交量萎缩，市场观望情绪浓厚。"
        
        # 情绪解读
        if fear_greed > 70:
            commentary += "<br><br>市场情绪偏贪婪，注意控制仓位，别追高。"
        elif fear_greed < 30:
            commentary += "<br><br>市场情绪偏恐惧，可能是布局机会，可以考虑逢低买入。"
        else:
            commentary += "<br><br>市场情绪中性，适合正常操作。"
        
        return commentary
    
    def _analyze_sectors(self, fund_scores: List[Dict]) -> List[Dict]:
        """分析板块热度"""
        # 定义板块映射
        sector_map = {
            '沪深300': '宽基', '中证500': '宽基', '创业板指': '宽基', '科创50': '宽基',
            '上证50': '宽基', '中证1000': '宽基',
            '中证白酒': '消费', '中证医疗': '医药', '中证新能源': '新能源',
            '中证半导体': '科技', '中证军工': '军工', '中证银行': '金融',
            '证券公司': '金融', '中证房地产': '地产', '中证人工智能': '科技',
            '中证传媒': '传媒', '纳斯达克100': '海外', '标普500': '海外', '恒生指数': '海外'
        }
        
        sectors = {}
        for fund in fund_scores:
            name = fund.get('fund_name', '')
            for key, sector in sector_map.items():
                if key in name:
                    if sector not in sectors:
                        sectors[sector] = {'total_score': 0, 'count': 0, 'funds': []}
                    sectors[sector]['total_score'] += fund.get('total_score', 50)
                    sectors[sector]['count'] += 1
                    sectors[sector]['funds'].append(fund)
                    break
        
        # 计算平均分
        result = []
        for sector, data in sectors.items():
            avg_score = data['total_score'] / data['count'] if data['count'] > 0 else 50
            result.append({
                'name': sector,
                'score': round(avg_score, 1),
                'fund_count': data['count'],
                'top_fund': max(data['funds'], key=lambda x: x.get('total_score', 0)) if data['funds'] else None
            })
        
        # 按分数排序
        result.sort(key=lambda x: x['score'], reverse=True)
        return result[:6]  # 返回前6个板块
    
    def _generate_sector_html(self, sectors: List[Dict]) -> str:
        """生成板块分析HTML"""
        if not sectors:
            return '<div class="empty-state">暂无板块数据</div>'
        
        html = ''
        for sector in sectors:
            name = sector['name']
            score = sector['score']
            
            # 根据分数设置样式
            score_class = ''
            if score >= 75:
                score_class = 'high'
                desc = '值得关注'
            elif score >= 60:
                desc = '表现良好'
            elif score >= 40:
                desc = '表现一般'
            else:
                score_class = 'low'
                desc = '暂时回避'
            
            html += f"""
            <div class="sector-item">
                <div class="sector-name">{name}</div>
                <div class="sector-score {score_class}">{score}分</div>
                <div class="sector-desc">{desc} · {sector['fund_count']}只基金</div>
            </div>
            """
        
        return html
    
    def _generate_recommended_funds_html(self, fund_scores: List[Dict]) -> str:
        """生成推荐基金HTML - 增强版，包含短期交易建议"""
        if not fund_scores:
            return '<div class="empty-state">暂无推荐</div>'
        
        # 获取评分最高的5只基金
        top_funds = sorted(fund_scores, key=lambda x: x.get('total_score', 0), reverse=True)[:5]
        
        html = ''
        for fund in top_funds:
            name = fund.get('fund_name', '未知')
            code = fund.get('fund_code', '')
            score = fund.get('total_score', 0)
            pe = fund.get('pe', 0)
            pe_pct = fund.get('pe_percentile', 50)
            
            # 确定推荐标签和仓位建议
            position_advice = self._generate_position_advice(fund)
            
            if score >= 75:
                badge_class = 'badge-buy'
                badge_text = '推荐买入'
            elif score >= 60:
                badge_class = 'badge-watch'
                badge_text = '值得关注'
            else:
                badge_class = 'badge-hold'
                badge_text = '可持有'
            
            # 生成交易计划
            trading_plan = self._generate_trading_plan(fund)
            
            # 生成详细推荐理由
            reasons = fund.get('reasons', [])
            reason_html = self._generate_fund_reasons_html(fund, reasons)
            
            html += f"""
            <div class="fund-item">
                <div class="fund-header">
                    <div class="fund-name">{name} ({code})</div>
                    <span class="fund-badge {badge_class}">{badge_text}</span>
                </div>
                
                <!-- 交易计划卡片 -->
                {trading_plan}
                
                <div class="fund-reason-list">
                    {reason_html}
                </div>
                <div class="fund-metrics">
                    <div class="metric">
                        <span class="metric-label">综合评分:</span>
                        <span class="metric-value">{score:.0f}分</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">市盈率:</span>
                        <span class="metric-value">{pe:.1f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">估值分位:</span>
                        <span class="metric-value">{pe_pct:.0f}%</span>
                    </div>
                </div>
            </div>
            """
        
        return html
    
    def _generate_position_advice(self, fund: Dict) -> str:
        """生成仓位建议"""
        score = fund.get('total_score', 50)
        pe_pct = fund.get('pe_percentile', 50)
        
        # 根据评分和估值给出仓位建议
        if score >= 80 and pe_pct < 30:
            return "建议仓位：15-20%（可重仓）"
        elif score >= 70 and pe_pct < 40:
            return "建议仓位：10-15%（可加仓）"
        elif score >= 60 and pe_pct < 50:
            return "建议仓位：5-10%（轻仓试探）"
        elif score >= 50:
            return "建议仓位：3-5%（观察仓）"
        else:
            return "建议仓位：暂不参与"
    
    def _generate_trading_plan(self, fund: Dict) -> str:
        """生成交易计划卡片"""
        name = fund.get('fund_name', '')
        score = fund.get('total_score', 50)
        pe_pct = fund.get('pe_percentile', 50)
        current_price = fund.get('current_price', 0)
        
        # 判断位置高低
        if pe_pct < 20:
            position = "🔴 历史低位"
            position_desc = "估值处于历史底部区域，安全边际高"
        elif pe_pct < 40:
            position = "🟡 相对低位"
            position_desc = "估值低于历史平均水平，具备配置价值"
        elif pe_pct > 80:
            position = "⚠️ 历史高位"
            position_desc = "估值处于历史高位，注意回调风险"
        elif pe_pct > 60:
            position = "🟠 相对高位"
            position_desc = "估值高于历史平均水平，谨慎追高"
        else:
            position = "⚪ 合理区间"
            position_desc = "估值处于历史中等水平"
        
        # 仓位建议
        position_advice = self._generate_position_advice(fund)
        
        # 目标收益和持有周期
        if score >= 75 and pe_pct < 40:
            target_return = "15-25%"
            hold_period = "1-3个月"
            sell_trigger = "估值修复至PE分位50%以上或涨幅达20%"
        elif score >= 65 and pe_pct < 50:
            target_return = "10-18%"
            hold_period = "2-4个月"
            sell_trigger = "估值回归合理区间或涨幅达15%"
        elif score >= 55:
            target_return = "8-12%"
            hold_period = "3-6个月"
            sell_trigger = "达到目标收益或趋势转弱"
        else:
            target_return = "5-10%"
            hold_period = "3-6个月"
            sell_trigger = "达到目标收益或出现更好的机会"
        
        # 事件驱动分析
        event_analysis = self._analyze_event_driver(fund)
        
        return f"""
        <div class="trading-plan-card">
            <div class="plan-header">
                <span class="plan-title">📋 交易计划</span>
                <span class="position-tag">{position}</span>
            </div>
            <div class="plan-content">
                <div class="plan-row">
                    <span class="plan-label">💰 仓位建议：</span>
                    <span class="plan-value highlight">{position_advice}</span>
                </div>
                <div class="plan-row">
                    <span class="plan-label">🎯 目标收益：</span>
                    <span class="plan-value">{target_return}</span>
                </div>
                <div class="plan-row">
                    <span class="plan-label">⏱️ 持有周期：</span>
                    <span class="plan-value">{hold_period}</span>
                </div>
                <div class="plan-row">
                    <span class="plan-label">🚪 卖出条件：</span>
                    <span class="plan-value">{sell_trigger}</span>
                </div>
                {event_analysis}
            </div>
            <div class="position-desc">{position_desc}</div>
        </div>
        """
    
    def _analyze_event_driver(self, fund: Dict) -> str:
        """分析事件驱动因素"""
        name = fund.get('fund_name', '')
        pe_pct = fund.get('pe_percentile', 50)
        trend_score = fund.get('trend_score', 50)
        
        events = []
        
        # 根据基金类型和估值判断可能的驱动事件
        if '白酒' in name:
            if pe_pct < 30:
                events.append("消费复苏预期下，白酒板块估值修复机会")
            elif pe_pct > 70:
                events.append("旺季过后需求回落，注意短期回调风险")
        elif '医药' in name or '医疗' in name:
            if pe_pct < 30:
                events.append("医药集采影响减弱，创新药政策边际改善")
            events.append("人口老龄化长期支撑医药需求")
        elif '新能源' in name:
            if pe_pct < 35:
                events.append("产业链价格触底，产能出清接近尾声")
            events.append("政策持续支持新能源发展")
        elif '半导体' in name or '芯片' in name:
            if pe_pct < 35:
                events.append("行业周期底部，国产替代逻辑持续")
            events.append("AI算力需求带动半导体景气度回升")
        elif '人工智能' in name or 'AI' in name:
            events.append("AI应用落地加速，算力需求持续增长")
        elif '恒生' in name or '港股' in name:
            if pe_pct < 25:
                events.append("港股估值处于历史极低水平，存在估值修复空间")
            events.append("美联储降息预期利好港股流动性")
        elif '纳斯达克' in name or '标普' in name:
            events.append("美股科技股业绩韧性较强")
        elif '银行' in name or '证券' in name:
            events.append("高股息策略下金融板块配置价值凸显")
        elif '军工' in name:
            events.append("国防预算增长，订单落地预期增强")
        
        # 技术面事件
        if trend_score >= 70:
            events.append("技术形态突破，资金流入明显")
        elif trend_score <= 30:
            events.append("短期超卖，存在技术性反弹机会")
        
        if events:
            event_text = "；".join(events[:2])  # 最多显示2个事件
            return f'''
                <div class="plan-row event-row">
                    <span class="plan-label">📰 驱动因素：</span>
                    <span class="plan-value">{event_text}</span>
                </div>
            '''
        return ""
    
    def _generate_fund_reasons_html(self, fund: Dict, reasons: List[str]) -> str:
        """生成基金详细推荐理由HTML"""
        html = '<ul class="reason-list">'
        
        # 1. 估值理由
        pe_pct = fund.get('pe_percentile', 50)
        if pe_pct < 20:
            html += f'<li class="reason-item"><span class="reason-icon">💰</span><span class="reason-text">估值极低：PE分位仅{pe_pct:.0f}%，处于历史低位，性价比较高</span></li>'
        elif pe_pct < 40:
            html += f'<li class="reason-item"><span class="reason-icon">💰</span><span class="reason-text">估值偏低：PE分位{pe_pct:.0f}%，低于历史平均水平</span></li>'
        elif pe_pct > 80:
            html += f'<li class="reason-item"><span class="reason-icon">⚠️</span><span class="reason-text">估值偏高：PE分位{pe_pct:.0f}%，处于历史高位，注意风险</span></li>'
        
        # 2. 趋势理由
        trend_score = fund.get('trend_score', 50)
        if trend_score >= 70:
            html += f'<li class="reason-item"><span class="reason-icon">📈</span><span class="reason-text">趋势向好：技术面评分{trend_score:.0f}分，处于上升通道</span></li>'
        elif trend_score <= 30:
            html += f'<li class="reason-item"><span class="reason-icon">📉</span><span class="reason-text">趋势偏弱：技术面评分{trend_score:.0f}分，短期承压</span></li>'
        
        # 3. 动量理由
        momentum = fund.get('momentum_score', 50)
        if momentum >= 70:
            html += f'<li class="reason-item"><span class="reason-icon">🚀</span><span class="reason-text">动量强劲：近期表现活跃，资金关注度高</span></li>'
        elif momentum <= 30:
            html += f'<li class="reason-item"><span class="reason-icon">😴</span><span class="reason-text">动量不足：近期表现平淡，缺乏资金推动</span></li>'
        
        # 4. 波动率理由
        volatility = fund.get('volatility_score', 50)
        if volatility >= 70:
            html += f'<li class="reason-item"><span class="reason-icon">⚡</span><span class="reason-text">波动较大：适合短线操作，注意控制风险</span></li>'
        elif volatility <= 30:
            html += f'<li class="reason-item"><span class="reason-icon">😌</span><span class="reason-text">波动较小：走势相对稳健，适合长期持有</span></li>'
        
        # 5. 添加原始reasons中的其他理由
        for reason in reasons[:2]:  # 最多显示2条原始理由
            if reason and len(reason) > 5:  # 过滤掉太短的
                html += f'<li class="reason-item"><span class="reason-icon">💡</span><span class="reason-text">{reason}</span></li>'
        
        html += '</ul>'
        return html
    
    def _generate_holdings_html(self, holdings: List[Dict]) -> str:
        """生成持仓列表HTML"""
        if not holdings:
            return '<div class="empty-state"><div class="icon">📭</div><div>暂无持仓数据</div></div>'
        
        html = ''
        for h in holdings:
            name = h.get('name', '未知基金')
            amount = h.get('amount', 0)
            return_pct = h.get('return_pct', 0)
            action = h.get('action', 'hold')
            
            tag_class = 'tag-hold'
            tag_text = '持有'
            if action == 'buy':
                tag_class = 'tag-buy'
                tag_text = '加仓'
            elif action == 'watch':
                tag_class = 'tag-watch'
                tag_text = '观望'
            
            return_class = 'up' if return_pct >= 0 else 'down'
            return_sign = '+' if return_pct >= 0 else ''
            
            html += f"""
            <div class="holding-row">
                <div class="holding-name">{name}</div>
                <div class="holding-amount">¥{amount:,.0f}</div>
                <div class="holding-return {return_class}">{return_sign}{return_pct:.2f}%</div>
                <span class="holding-tag {tag_class}">{tag_text}</span>
            </div>
            """
        
        return html
    
    def _generate_action_html(self, holdings: List[Dict]) -> str:
        """生成行动建议HTML"""
        if not holdings:
            return '<div class="empty-state"><div class="icon">🤔</div><div>暂无持仓建议</div></div>'
        
        buy_list = [h for h in holdings if h.get('action') == 'buy']
        watch_list = [h for h in holdings if h.get('action') == 'watch']
        
        html = ''
        
        if buy_list:
            names = '、'.join([h.get('name', '未知')[:12] for h in buy_list[:2]])
            if len(buy_list) > 2:
                names += f' 等{len(buy_list)}只'
            
            reasons = []
            for h in buy_list[:2]:
                reason = h.get('reason', '')
                if reason:
                    reasons.append(reason)
            
            html += f"""
            <div class="action-card buy">
                <div class="action-title">🔴 可以考虑加仓</div>
                <div class="action-text">
                    <span class="action-funds">{names}</span><br><br>
                    {'；'.join(reasons) if reasons else '这些基金目前估值较低，可以考虑分批买入摊薄成本。'}
                </div>
            </div>
            """
        
        if watch_list:
            names = '、'.join([h.get('name', '未知')[:12] for h in watch_list[:2]])
            if len(watch_list) > 2:
                names += f' 等{len(watch_list)}只'
            
            html += f"""
            <div class="action-card watch">
                <div class="action-title">🟡 先观望一下</div>
                <div class="action-text">
                    <span class="action-funds">{names}</span><br><br>
                    目前趋势还不明朗，建议再等等，不要急着操作。
                </div>
            </div>
            """
        
        if not html:
            html = """
            <div class="action-card hold">
                <div class="action-title">🔵 继续持有</div>
                <div class="action-text">
                    当前持仓整体表现平稳，没有特别需要操作的。建议耐心持有，等待更好的买卖时机。
                </div>
            </div>
            """
        
        return html
    
    def _generate_opportunities_html(self, opportunities: List[Dict]) -> str:
        """生成机会列表HTML"""
        if not opportunities:
            return '<div class="empty-state"><div class="icon">🔍</div><div>暂时没有发现好的买入机会</div></div>'
        
        html = ''
        for opp in opportunities[:3]:
            name = opp.get('name', '未知')
            score = opp.get('score', 0)
            reason = opp.get('reason', '')
            buy_price = opp.get('buy_price', 'N/A')
            target = opp.get('target_price', 'N/A')
            
            html += f"""
            <div class="opportunity-card">
                <div class="opp-header">
                    <div class="opp-name">{name}</div>
                    <div class="opp-score">{score}分</div>
                </div>
                <div class="opp-reason">{reason}</div>
                <div class="opp-prices">
                    <div><span class="label">建议买入:</span> <span class="value">{buy_price}</span></div>
                    <div><span class="label">目标价位:</span> <span class="value">{target}</span></div>
                </div>
            </div>
            """
        
        return html
    
    def _generate_fund_flow_html(self, market_data: Dict) -> str:
        """生成资金流向HTML"""
        html = ''
        
        # 北向资金
        north_flow = market_data.get('north_money_flow', 0)
        north_5d = market_data.get('north_money_5d', 0)
        north_class = 'up' if north_flow >= 0 else 'down'
        north_icon = '📈' if north_flow >= 0 else '📉'
        north_text = '净流入' if north_flow >= 0 else '净流出'
        
        html += f"""
        <div class="flow-item" style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">🌊 北向资金（今日）</div>
            <div style="font-size: 16px; font-weight: 600;" class="{north_class}">
                {north_icon} {abs(north_flow):.1f}亿
            </div>
            <div style="font-size: 11px; color: #999; margin-top: 2px;">
                {north_text} · 5日累计: {'+' if north_5d >= 0 else ''}{north_5d:.1f}亿
            </div>
        </div>
        """
        
        # 主力资金
        main_flow = market_data.get('main_money_flow', 0)
        main_5d = market_data.get('main_money_5d', 0)
        main_class = 'up' if main_flow >= 0 else 'down'
        main_icon = '📈' if main_flow >= 0 else '📉'
        main_text = '净流入' if main_flow >= 0 else '净流出'
        
        html += f"""
        <div class="flow-item" style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">🏦 主力资金（今日）</div>
            <div style="font-size: 16px; font-weight: 600;" class="{main_class}">
                {main_icon} {abs(main_flow):.1f}亿
            </div>
            <div style="font-size: 11px; color: #999; margin-top: 2px;">
                {main_text} · 5日累计: {'+' if main_5d >= 0 else ''}{main_5d:.1f}亿
            </div>
        </div>
        """
        
        # 融资余额
        margin = market_data.get('margin_balance', 0)
        margin_change = market_data.get('margin_change', 0)
        margin_class = 'up' if margin_change >= 0 else 'down'
        margin_icon = '📈' if margin_change >= 0 else '📉'
        
        html += f"""
        <div class="flow-item" style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">💳 融资余额</div>
            <div style="font-size: 16px; font-weight: 600; color: #2c3e50;">
                {margin:.0f}亿
            </div>
            <div style="font-size: 11px; color: #999; margin-top: 2px;" class="{margin_class}">
                {margin_icon} 较昨日{'+' if margin_change >= 0 else ''}{margin_change:.1f}亿
            </div>
        </div>
        """
        
        # 成交量比
        vol_ratio = market_data.get('volume_ratio', 1.0)
        vol_status = '放量' if vol_ratio > 1.2 else '缩量' if vol_ratio < 0.8 else '平量'
        vol_color = '#e74c3c' if vol_ratio > 1.2 else '#27ae60' if vol_ratio < 0.8 else '#95a5a6'
        
        html += f"""
        <div class="flow-item" style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">📊 成交量比</div>
            <div style="font-size: 16px; font-weight: 600; color: {vol_color};">
                {vol_ratio:.2f}x
            </div>
            <div style="font-size: 11px; color: #999; margin-top: 2px;">
                {vol_status} · 相对5日均量
            </div>
        </div>
        """
        
        return html


def generate_visual_report_v3(market_data: Dict, portfolio_analysis: Dict, 
                              opportunities: List[Dict], fund_scores: List[Dict]) -> str:
    """生成可视化报告V3"""
    generator = VisualReportGeneratorV3()
    return generator.generate_report(market_data, portfolio_analysis, opportunities, fund_scores)
