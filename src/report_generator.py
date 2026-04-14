"""
报告生成模块
生成每日基金分析报告，支持HTML和文本格式
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
from jinja2 import Template
import os


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_html_report(self, 
                            scores: List[Dict],
                            market_overview: Dict,
                            date: str = None) -> str:
        """
        生成HTML格式的报告
        
        Args:
            scores: 基金评分列表
            market_overview: 市场概览数据
            date: 报告日期
            
        Returns:
            HTML字符串
        """
        if date is None:
            date = datetime.now().strftime("%Y年%m月%d日")
        
        # 分类基金
        buy_list = [s for s in scores if s['total_score'] >= 75]
        watch_list = [s for s in scores if 60 <= s['total_score'] < 75]
        avoid_list = [s for s in scores if s['total_score'] < 50]
        
        # 按评分排序
        buy_list = sorted(buy_list, key=lambda x: x['total_score'], reverse=True)
        watch_list = sorted(watch_list, key=lambda x: x['total_score'], reverse=True)
        
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金理财日报 - {{ date }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .date { opacity: 0.9; font-size: 14px; }
        .content { padding: 30px; }
        .section { margin-bottom: 30px; }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .market-overview {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .market-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .market-item .label { color: #666; font-size: 12px; margin-bottom: 5px; }
        .market-item .value { font-size: 20px; font-weight: 600; }
        .market-item .change { font-size: 12px; margin-top: 5px; }
        .positive { color: #f44336; }
        .negative { color: #4caf50; }
        .fund-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }
        .fund-card:hover { transform: translateX(5px); }
        .fund-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .fund-name { font-size: 16px; font-weight: 600; }
        .fund-code { color: #999; font-size: 12px; margin-left: 8px; }
        .score-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        .score-high { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .score-medium { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .score-low { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .fund-details {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 12px;
        }
        .detail-item {
            background: white;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }
        .detail-item .label { font-size: 11px; color: #999; }
        .detail-item .value { font-size: 13px; font-weight: 600; color: #333; }
        .recommendation {
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .rec-title { font-weight: 600; color: #667eea; margin-bottom: 5px; }
        .rec-text { font-size: 14px; color: #555; }
        .reasons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .reason-tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
        }
        .risks {
            margin-top: 10px;
            padding: 10px;
            background: #fff3e0;
            border-radius: 6px;
            font-size: 12px;
            color: #e65100;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
        }
        .disclaimer {
            background: #fff8e1;
            border: 1px solid #ffe082;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-size: 12px;
            color: #f57c00;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 智能基金理财日报</h1>
            <div class="date">{{ date }}</div>
        </div>
        
        <div class="content">
            <!-- 市场概览 -->
            <div class="section">
                <div class="section-title">📊 市场概览</div>
                <div class="market-overview">
                    <div class="market-item">
                        <div class="label">上证指数</div>
                        <div class="value">{{ market_overview.sh_index }}</div>
                        <div class="change {{ 'positive' if market_overview.sh_change > 0 else 'negative' }}">
                            {{ "+%.2f" % market_overview.sh_change if market_overview.sh_change > 0 else "%.2f" % market_overview.sh_change }}%
                        </div>
                    </div>
                    <div class="market-item">
                        <div class="label">深证成指</div>
                        <div class="value">{{ market_overview.sz_index }}</div>
                        <div class="change {{ 'positive' if market_overview.sz_change > 0 else 'negative' }}">
                            {{ "+%.2f" % market_overview.sz_change if market_overview.sz_change > 0 else "%.2f" % market_overview.sz_change }}%
                        </div>
                    </div>
                    <div class="market-item">
                        <div class="label">创业板指</div>
                        <div class="value">{{ market_overview.cy_index }}</div>
                        <div class="change {{ 'positive' if market_overview.cy_change > 0 else 'negative' }}">
                            {{ "+%.2f" % market_overview.cy_change if market_overview.cy_change > 0 else "%.2f" % market_overview.cy_change }}%
                        </div>
                    </div>
                    <div class="market-item">
                        <div class="label">北向资金</div>
                        <div class="value">{{ "%.1f" % market_overview.north_money }}亿</div>
                        <div class="change {{ 'positive' if market_overview.north_money > 0 else 'negative' }}">
                            {{ "流入" if market_overview.north_money > 0 else "流出" }}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 推荐买入 -->
            <div class="section">
                <div class="section-title">🎯 推荐买入 (评分≥75)</div>
                {% if buy_list %}
                    {% for fund in buy_list %}
                    <div class="fund-card">
                        <div class="fund-header">
                            <div>
                                <span class="fund-name">{{ fund.fund_name }}</span>
                                <span class="fund-code">{{ fund.fund_code }}</span>
                            </div>
                            <span class="score-badge score-high">{{ fund.total_score }}分</span>
                        </div>
                        <div class="fund-details">
                            <div class="detail-item">
                                <div class="label">估值评分</div>
                                <div class="value">{{ fund.valuation_score }}</div>
                            </div>
                            <div class="detail-item">
                                <div class="label">技术评分</div>
                                <div class="value">{{ fund.technical_score }}</div>
                            </div>
                            <div class="detail-item">
                                <div class="label">资金评分</div>
                                <div class="value">{{ fund.fund_flow_score }}</div>
                            </div>
                        </div>
                        <div class="recommendation">
                            <div class="rec-title">💡 {{ fund.recommendation }} | {{ fund.position_suggestion }}</div>
                        </div>
                        <div class="reasons">
                            {% for reason in fund.reasons %}
                            <span class="reason-tag">{{ reason }}</span>
                            {% endfor %}
                        </div>
                        {% if fund.risks %}
                        <div class="risks">
                            ⚠️ 风险提示: {{ fund.risks | join(', ') }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">暂无推荐买入的基金</div>
                {% endif %}
            </div>
            
            <!-- 关注列表 -->
            <div class="section">
                <div class="section-title">👀 关注列表 (评分60-75)</div>
                {% if watch_list %}
                    {% for fund in watch_list %}
                    <div class="fund-card" style="border-left-color: #f5576c;">
                        <div class="fund-header">
                            <div>
                                <span class="fund-name">{{ fund.fund_name }}</span>
                                <span class="fund-code">{{ fund.fund_code }}</span>
                            </div>
                            <span class="score-badge score-medium">{{ fund.total_score }}分</span>
                        </div>
                        <div class="recommendation">
                            <div class="rec-title">💡 {{ fund.recommendation }}</div>
                        </div>
                        <div class="reasons">
                            {% for reason in fund.reasons[:3] %}
                            <span class="reason-tag">{{ reason }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">暂无关注基金</div>
                {% endif %}
            </div>
            
            <!-- 免责声明 -->
            <div class="disclaimer">
                <strong>⚠️ 免责声明：</strong>本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
                过往业绩不代表未来表现，请根据自身风险承受能力做出投资决策。
            </div>
        </div>
        
        <div class="footer">
            智能基金理财顾问系统 | 生成时间: {{ datetime.now().strftime("%Y-%m-%d %H:%M") }}
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        html = template.render(
            date=date,
            market_overview=market_overview,
            buy_list=buy_list,
            watch_list=watch_list,
            avoid_list=avoid_list,
            datetime=datetime
        )
        
        return html
    
    def generate_text_report(self,
                            scores: List[Dict],
                            market_overview: Dict,
                            big_player_insights: Dict = None,
                            sector_flow: Dict = None,
                            date: str = None) -> str:
        """
        生成纯文本格式的报告（增强版，用于微信/邮件推送）
        """
        if date is None:
            date = datetime.now().strftime("%Y年%m月%d日")
        
        buy_list = [s for s in scores if s['total_score'] >= 75]
        watch_list = [s for s in scores if 60 <= s['total_score'] < 75]
        low_valuation = [s for s in scores if s.get('pe_percentile', 50) < 20]
        
        buy_list = sorted(buy_list, key=lambda x: x['total_score'], reverse=True)
        watch_list = sorted(watch_list, key=lambda x: x['total_score'], reverse=True)
        
        lines = [
            f"🎯 基金理财日报 - {date}",
            "",
            "📊 市场概览",
            f"• 上证指数: {market_overview['sh_index']} ({market_overview['sh_change']:+.2f}%)",
            f"• 深证成指: {market_overview['sz_index']} ({market_overview['sz_change']:+.2f}%)",
            f"• 创业板指: {market_overview['cy_index']} ({market_overview['cy_change']:+.2f}%)",
            f"• 北向资金: {market_overview.get('north_money', 0):+.1f}亿",
            f"• 涨跌家数: {market_overview.get('up_count', 0)}↑ / {market_overview.get('down_count', 0)}↓",
            f"• 恐贪指数: {market_overview.get('fear_greed_index', 50):.1f}",
        ]
        
        # 添加资金面信息
        if market_overview.get('north_money_5d'):
            lines.append(f"• 5日北向: {market_overview['north_money_5d']:+.1f}亿")
        if market_overview.get('main_money_flow'):
            lines.append(f"• 主力资金: {market_overview['main_money_flow']:+.1f}亿")
        if market_overview.get('margin_change'):
            lines.append(f"• 融资变化: {market_overview['margin_change']:+.1f}亿")
        
        lines.append("")
        
        # 大佬动态
        if big_player_insights and big_player_insights.get('大佬动态'):
            lines.extend([
                "👑 大佬最新动态",
            ])
            for insight in big_player_insights['大佬动态'][:3]:
                action_emoji = "📈" if insight.get('操作') == '加仓' else "📉" if insight.get('操作') == '减仓' else "🔄"
                lines.append(f"• {insight['大佬']}: {action_emoji} {insight['操作']} {insight['标的']}")
            lines.append("")
        
        # 热门赛道共识
        if big_player_insights and big_player_insights.get('热门赛道共识'):
            lines.extend([
                "🔥 热门赛道共识",
            ])
            for sector, consensus in list(big_player_insights['热门赛道共识'].items())[:3]:
                bullish = consensus.get('看多', 0)
                bearish = consensus.get('看空', 0)
                total = bullish + bearish
                if total > 0:
                    ratio = int(bullish / total * 100)
                    lines.append(f"• {sector}: {ratio}%看多 - {consensus.get('共识', '中性')}")
            lines.append("")
        
        # 板块资金流向
        if sector_flow and sector_flow.get('top_inflow_sectors'):
            lines.extend([
                "💰 板块资金流向",
                "流入前3:",
            ])
            for sector in sector_flow['top_inflow_sectors'][:3]:
                lines.append(f"• {sector['name']}: +{sector['main_inflow']:.1f}亿")
            lines.append("")
        
        # 推荐买入
        lines.extend([
            "🎯 今日推荐买入（评分≥75）",
        ])
        if buy_list:
            for i, fund in enumerate(buy_list[:5], 1):
                lines.extend([
                    f"\n{i}. {fund['fund_name']} - {fund['total_score']}分",
                    f"   建议: {fund['position_suggestion']}",
                ])
                if fund.get('research_summary'):
                    lines.append(f"   理由: {fund['research_summary']}")
                # 技术面信号
                tech_signals = []
                if fund.get('rsi', 50) < 30:
                    tech_signals.append("RSI超卖")
                if fund.get('pattern_signals'):
                    tech_signals.extend(fund['pattern_signals'][:2])
                if tech_signals:
                    lines.append(f"   技术: {' | '.join(tech_signals)}")
                # 大佬共识
                if fund.get('big_player_consensus'):
                    consensus = fund['big_player_consensus']
                    if consensus.get('bullish_ratio', 0.5) > 0.6:
                        lines.append(f"   共识: {int(consensus['bullish_ratio']*100)}%大佬看多")
        else:
            lines.append("暂无强烈推荐买入的基金")
        
        lines.append("")
        
        # 关注列表
        if watch_list:
            lines.extend([
                "👀 值得关注（评分60-75）",
            ])
            for fund in watch_list[:5]:
                line = f"• {fund['fund_name']} - {fund['total_score']}分"
                if fund.get('research_summary'):
                    line += f" ({fund['research_summary'][:20]}...)"
                lines.append(line)
            lines.append("")
        
        # 估值低位
        if low_valuation:
            lines.extend([
                "📉 估值历史低位（PE分位<20%）",
            ])
            for fund in low_valuation[:5]:
                lines.append(f"• {fund['fund_name']}: PE分位{fund.get('pe_percentile', 0):.1f}%")
            lines.append("")
        
        # 操作建议
        lines.extend([
            "💡 操作建议",
        ])
        
        # 根据市场情况给出建议
        fear_greed = market_overview.get('fear_greed_index', 50)
        if fear_greed > 80:
            lines.append("市场情绪过热，建议减仓或观望")
        elif fear_greed < 20:
            lines.append("市场极度恐慌，可能是布局机会")
        elif buy_list:
            lines.append(f"今日有{buy_list[0]['fund_name']}等{len(buy_list)}只基金评分较高，可考虑分批建仓")
        else:
            lines.append("市场震荡，建议保持现有仓位，等待更好时机")
        
        lines.extend([
            "",
            "⚠️ 免责声明: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。",
        ])
        
        return "\n".join(lines)
    
    def save_report(self, html_content: str, date: str = None) -> str:
        """
        保存报告到文件
        
        Returns:
            保存的文件路径
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        filename = f"fund_report_{date}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath


if __name__ == "__main__":
    # 测试报告生成
    generator = ReportGenerator()
    
    # 模拟数据
    mock_scores = [
        {
            'fund_code': '000300',
            'fund_name': '沪深300',
            'total_score': 85.5,
            'valuation_score': 92.0,
            'technical_score': 78.5,
            'fund_flow_score': 75.0,
            'fundamental_score': 88.0,
            'sentiment_score': 82.0,
            'recommendation': '强烈建议买入',
            'position_suggestion': '可建仓30-50%',
            'reasons': ['极度低估 (PE分位8.5%)', 'RSI超卖(32.0)', 'MACD金叉信号'],
            'risks': ['暂无重大风险']
        },
        {
            'fund_code': '399989',
            'fund_name': '中证医疗',
            'total_score': 78.0,
            'valuation_score': 88.0,
            'technical_score': 72.0,
            'fund_flow_score': 65.0,
            'fundamental_score': 80.0,
            'sentiment_score': 70.0,
            'recommendation': '建议买入',
            'position_suggestion': '可建仓20-30%',
            'reasons': ['低估区间 (PE分位15.2%)', '价格触及布林带下轨'],
            'risks': ['波动率较高(28%)']
        },
    ]
    
    market_overview = {
        'sh_index': 3050.32,
        'sh_change': -0.45,
        'sz_index': 9850.15,
        'sz_change': -0.62,
        'cy_index': 1920.50,
        'cy_change': -0.85,
        'north_money': 25.8
    }
    
    # 生成HTML报告
    html = generator.generate_html_report(mock_scores, market_overview)
    filepath = generator.save_report(html)
    print(f"报告已保存: {filepath}")
    
    # 生成文本报告
    text = generator.generate_text_report(mock_scores, market_overview)
    print("\n" + "="*50)
    print(text)
