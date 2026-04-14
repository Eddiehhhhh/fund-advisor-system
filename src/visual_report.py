#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化报告生成器 - 大白话版
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class VisualReportGenerator:
    """生成可视化HTML报告"""
    
    def __init__(self):
        self.colors = {
            'up': '#e74c3c',      # 涨 - 红色
            'down': '#27ae60',    # 跌 - 绿色
            'neutral': '#95a5a6', # 中性
            'primary': '#3498db', # 主色
            'warning': '#f39c12', # 警告
            'bg': '#f8f9fa',      # 背景
            'card': '#ffffff',    # 卡片
        }
    
    def generate_report(self, 
                       market_data: Dict,
                       portfolio_analysis: Dict,
                       opportunities: List[Dict],
                       fund_scores: List[Dict]) -> str:
        """生成完整报告"""
        
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
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        
        /* 头部 */
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px 20px; 
            border-radius: 16px; 
            margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .date {{ opacity: 0.9; font-size: 14px; }}
        
        /* 卡片 */
        .card {{ 
            background: {self.colors['card']}; 
            border-radius: 12px; 
            padding: 20px; 
            margin-bottom: 16px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .card-title {{ 
            font-size: 18px; 
            font-weight: 600; 
            margin-bottom: 16px; 
            display: flex; 
            align-items: center; 
            gap: 8px;
        }}
        
        /* 市场概况 */
        .market-grid {{ 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 12px; 
            text-align: center;
        }}
        .market-item {{ padding: 16px; background: #f8f9fa; border-radius: 10px; }}
        .market-item .label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
        .market-item .value {{ font-size: 22px; font-weight: 700; }}
        .market-item .change {{ font-size: 13px; margin-top: 4px; }}
        
        /* 持仓概览 */
        .portfolio-summary {{ 
            display: flex; 
            justify-content: space-around; 
            padding: 20px 0;
            border-bottom: 1px solid #eee;
            margin-bottom: 20px;
        }}
        .summary-item {{ text-align: center; }}
        .summary-item .number {{ 
            font-size: 28px; 
            font-weight: 700; 
            color: {self.colors['primary']};
        }}
        .summary-item .number.negative {{ color: {self.colors['down']}; }}
        .summary-item .number.positive {{ color: {self.colors['up']}; }}
        .summary-item .label {{ font-size: 13px; color: #666; margin-top: 4px; }}
        
        /* 持仓列表 */
        .holding-item {{ 
            display: flex; 
            align-items: center; 
            padding: 14px 0; 
            border-bottom: 1px solid #f0f0f0;
        }}
        .holding-item:last-child {{ border-bottom: none; }}
        .holding-info {{ flex: 1; }}
        .holding-name {{ font-weight: 600; font-size: 15px; margin-bottom: 4px; }}
        .holding-tag {{ 
            display: inline-block; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-size: 11px;
            margin-right: 6px;
        }}
        .tag-buy {{ background: #ffe0e0; color: #c0392b; }}
        .tag-hold {{ background: #e0f0ff; color: #2980b9; }}
        .tag-watch {{ background: #fff3e0; color: #e67e22; }}
        .tag-sell {{ background: #e8e8e8; color: #7f8c8d; }}
        
        .holding-amount {{ text-align: right; }}
        .holding-amount .value {{ font-weight: 600; font-size: 15px; }}
        .holding-amount .return {{ font-size: 13px; margin-top: 2px; }}
        
        /* 建议卡片 */
        .advice-box {{ 
            padding: 16px; 
            border-radius: 10px; 
            margin-bottom: 12px;
        }}
        .advice-buy {{ background: #fff5f5; border-left: 4px solid {self.colors['up']}; }}
        .advice-hold {{ background: #f0f8ff; border-left: 4px solid {self.colors['primary']}; }}
        .advice-watch {{ background: #fffbf0; border-left: 4px solid {self.colors['warning']}; }}
        
        .advice-title {{ font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }}
        .advice-text {{ font-size: 14px; color: #555; line-height: 1.7; }}
        
        /* 机会列表 */
        .opportunity-item {{ 
            padding: 16px; 
            background: #f8f9fa; 
            border-radius: 10px; 
            margin-bottom: 12px;
        }}
        .opp-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .opp-name {{ font-weight: 600; font-size: 15px; }}
        .opp-score {{ 
            background: {self.colors['primary']}; 
            color: white; 
            padding: 4px 10px; 
            border-radius: 20px; 
            font-size: 12px;
            font-weight: 600;
        }}
        .opp-reason {{ font-size: 13px; color: #666; margin-bottom: 8px; }}
        .opp-target {{ 
            display: flex; 
            gap: 20px; 
            font-size: 13px;
        }}
        .opp-target span {{ color: #888; }}
        .opp-target strong {{ color: #333; }}
        
        /* 图表容器 */
        .chart-container {{ 
            position: relative; 
            height: 250px; 
            margin: 20px 0;
        }}
        
        /* 底部 */
        .footer {{ 
            text-align: center; 
            padding: 30px 20px; 
            color: #999; 
            font-size: 12px;
        }}
        
        /* 涨跌颜色 */
        .up {{ color: {self.colors['up']}; }}
        .down {{ color: {self.colors['down']}; }}
        
        /* 响应式 */
        @media (max-width: 600px) {{
            .market-grid {{ grid-template-columns: 1fr; }}
            .portfolio-summary {{ flex-direction: column; gap: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📊 基金理财日报</h1>
            <div class="date">{datetime.now().strftime('%Y年%m月%d日')}</div>
        </div>
        
        <!-- 市场概况 -->
        <div class="card">
            <div class="card-title">📈 今天市场怎么样</div>
            <div class="market-grid">
                <div class="market-item">
                    <div class="label">上证指数</div>
                    <div class="value">{market_data.get('sh_index', 'N/A')}</div>
                    <div class="change {'up' if market_data.get('sh_change', 0) >= 0 else 'down'}">{market_data.get('sh_change', 0):+.2f}%</div>
                </div>
                <div class="market-item">
                    <div class="label">涨跌家数</div>
                    <div class="value" style="font-size: 16px;">{market_data.get('up_count', 0)}↑ {market_data.get('down_count', 0)}↓</div>
                    <div class="change">{market_data.get('up_ratio', 0):.0f}%股票上涨</div>
                </div>
                <div class="market-item">
                    <div class="label">市场情绪</div>
                    <div class="value" style="font-size: 16px;">{market_data.get('sentiment', '中性')}</div>
                    <div class="change">恐贪指数: {market_data.get('fear_greed', 50)}</div>
                </div>
            </div>
        </div>
        
        <!-- 持仓概览 -->
        <div class="card">
            <div class="card-title">💰 我的持仓情况</div>
            <div class="portfolio-summary">
                <div class="summary-item">
                    <div class="number">¥{portfolio_analysis.get('total_value', 0):,.0f}</div>
                    <div class="label">总持仓</div>
                </div>
                <div class="summary-item">
                    <div class="number {'positive' if portfolio_analysis.get('total_return', 0) >= 0 else 'negative'}">
                        {'+' if portfolio_analysis.get('total_return', 0) >= 0 else ''}¥{portfolio_analysis.get('total_return', 0):,.0f}
                    </div>
                    <div class="label">总盈亏</div>
                </div>
                <div class="summary-item">
                    <div class="number {'positive' if portfolio_analysis.get('total_return_pct', 0) >= 0 else 'negative'}">
                        {portfolio_analysis.get('total_return_pct', 0):+.2f}%
                    </div>
                    <div class="label">收益率</div>
                </div>
            </div>
            
            <div style="margin-top: 10px;">
                {self._generate_holdings_html(portfolio_analysis.get('holdings', []))}
            </div>
        </div>
        
        <!-- 操作建议 -->
        <div class="card">
            <div class="card-title">💡 今天该做什么</div>
            {self._generate_advice_html(portfolio_analysis.get('holdings', []))}
        </div>
        
        <!-- 发现的机会 -->
        <div class="card">
            <div class="card-title">🎯 有哪些买入机会</div>
            {self._generate_opportunities_html(opportunities[:5])}
        </div>
        
        <!-- 持仓分布图 -->
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
                labels: {json.dumps([h.get('name', '未知') for h in portfolio_analysis.get('holdings', [])[:8]])},
                datasets: [{{
                    data: {json.dumps([h.get('amount', 0) for h in portfolio_analysis.get('holdings', [])[:8]])},
                    backgroundColor: [
                        '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
                        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
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
    
    def _generate_holdings_html(self, holdings: List[Dict]) -> str:
        """生成持仓列表HTML"""
        if not holdings:
            return '<p style="color: #999; text-align: center;">暂无持仓数据</p>'
        
        html = ''
        for h in holdings:
            name = h.get('name', '未知基金')
            amount = h.get('amount', 0)
            return_pct = h.get('return_pct', 0)
            action = h.get('action', 'hold')
            
            # 建议标签
            tag_class = 'tag-hold'
            tag_text = '持有'
            if action == 'buy':
                tag_class = 'tag-buy'
                tag_text = '加仓'
            elif action == 'watch':
                tag_class = 'tag-watch'
                tag_text = '观望'
            elif action == 'sell':
                tag_class = 'tag-sell'
                tag_text = '减仓'
            
            return_class = 'up' if return_pct >= 0 else 'down'
            return_sign = '+' if return_pct >= 0 else ''
            
            html += f"""
            <div class="holding-item">
                <div class="holding-info">
                    <div class="holding-name">{name}</div>
                    <div>
                        <span class="holding-tag {tag_class}">{tag_text}</span>
                        <span style="font-size: 12px; color: #999;">持仓 ¥{amount:,.0f}</span>
                    </div>
                </div>
                <div class="holding-amount">
                    <div class="value {return_class}">{return_sign}{return_pct:.2f}%</div>
                    <div class="return {return_class}">{return_sign}¥{h.get('return_value', 0):,.0f}</div>
                </div>
            </div>
            """
        
        return html
    
    def _generate_advice_html(self, holdings: List[Dict]) -> str:
        """生成操作建议HTML"""
        if not holdings:
            return '<p style="color: #999;">暂无持仓建议</p>'
        
        # 找出需要重点关注的
        buy_list = [h for h in holdings if h.get('action') == 'buy']
        watch_list = [h for h in holdings if h.get('action') == 'watch']
        
        html = ''
        
        # 加仓建议
        if buy_list:
            names = '、'.join([h.get('name', '未知')[:10] for h in buy_list[:3]])
            reasons = []
            for h in buy_list[:2]:
                reason = h.get('reason', '')
                if reason:
                    reasons.append(f"<b>{h.get('name', '未知')[:8]}</b>：{reason}")
            
            html += f"""
            <div class="advice-box advice-buy">
                <div class="advice-title">🔴 可以考虑加仓</div>
                <div class="advice-text">
                    <b>{names}</b> 等{buy_list.__len__()}只基金目前估值较低，可以考虑分批买入摊薄成本。<br><br>
                    {'<br>'.join(reasons)}
                </div>
            </div>
            """
        
        # 观望建议
        if watch_list:
            names = '、'.join([h.get('name', '未知')[:10] for h in watch_list[:3]])
            html += f"""
            <div class="advice-box advice-watch">
                <div class="advice-title">🟡 先观望一下</div>
                <div class="advice-text">
                    <b>{names}</b> 目前趋势还不明朗，建议再等等，不要急着操作。
                </div>
            </div>
            """
        
        # 默认建议
        if not html:
            html = """
            <div class="advice-box advice-hold">
                <div class="advice-title">🔵 继续持有</div>
                <div class="advice-text">
                    当前持仓整体表现平稳，没有特别需要操作的。建议耐心持有，等待更好的买卖时机。
                </div>
            </div>
            """
        
        return html
    
    def _generate_opportunities_html(self, opportunities: List[Dict]) -> str:
        """生成机会列表HTML"""
        if not opportunities:
            return '<p style="color: #999; text-align: center;">暂时没有发现好的买入机会</p>'
        
        html = ''
        for opp in opportunities[:5]:
            name = opp.get('name', '未知')
            score = opp.get('score', 0)
            reason = opp.get('reason', '')
            buy_price = opp.get('buy_price', 'N/A')
            target = opp.get('target_price', 'N/A')
            
            html += f"""
            <div class="opportunity-item">
                <div class="opp-header">
                    <div class="opp-name">{name}</div>
                    <div class="opp-score">{score}分</div>
                </div>
                <div class="opp-reason">{reason}</div>
                <div class="opp-target">
                    <div>建议买入: <strong>{buy_price}</strong></div>
                    <div>目标价位: <strong>{target}</strong></div>
                </div>
            </div>
            """
        
        return html


# 便捷函数
def generate_visual_report(market_data: Dict, portfolio_analysis: Dict, 
                          opportunities: List[Dict], fund_scores: List[Dict]) -> str:
    """生成可视化报告"""
    generator = VisualReportGenerator()
    return generator.generate_report(market_data, portfolio_analysis, opportunities, fund_scores)
