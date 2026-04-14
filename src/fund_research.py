"""
基金调研模块
整合基金博主观点、机构研报、赛道热度等信息
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ResearchInsight:
    """调研洞察"""
    source: str           # 来源
    author: str          # 作者
    content: str         # 内容摘要
    sentiment: str       # 情绪: bullish/bearish/neutral
    date: str            # 发布日期
    relevance: float     # 相关度 0-1


class FundResearch:
    """基金调研分析器"""
    
    def __init__(self):
        # 知名基金博主/机构列表
        self.trusted_sources = [
            "银行螺丝钉",
            "ETF拯救世界",
            "望京博格",
            "持有封基",
            "老罗话指数投资",
            "华夏基金",
            "易方达基金",
            "南方基金",
            "嘉实基金",
            "广发基金",
            "富国基金",
            "张坤",  # 易方达蓝筹
            "刘彦春",  # 景顺长城
            "朱少醒",  # 富国天惠
            "谢治宇",  # 兴全合宜
            "葛兰",  # 中欧医疗
            "蔡嵩松",  # 诺安成长（半导体）
        ]
        
        # 赛道热度缓存
        self.sector_heat_cache = {}
        self.cache_time = None
        
        # 大佬最新调仓观点（模拟实时数据）
        self.latest_insights = self._load_latest_insights()
    
    def _load_latest_insights(self) -> Dict:
        """加载最新的大佬观点和调仓动态"""
        return {
            "日期": "2026-04-11",
            "市场共识": "震荡分化，结构性机会",
            "大佬动态": [
                {
                    "大佬": "ETF拯救世界",
                    "操作": "加仓",
                    "标的": "沪深300、中证500",
                    "理由": "估值处于历史低位，长期配置价值凸显",
                    "信心度": 0.85
                },
                {
                    "大佬": "银行螺丝钉",
                    "操作": "定投",
                    "标的": "中证医疗、中证白酒",
                    "理由": "医疗估值历史低位，白酒库存去化接近尾声",
                    "信心度": 0.75
                },
                {
                    "大佬": "望京博格",
                    "操作": "加仓",
                    "标的": "中证半导体",
                    "理由": "周期底部+国产替代加速，业绩修复可期",
                    "信心度": 0.80
                },
                {
                    "大佬": "持有封基",
                    "操作": "减仓",
                    "标的": "中证新能源",
                    "理由": "产能过剩问题仍在，短期谨慎",
                    "信心度": 0.60
                },
                {
                    "大佬": "张坤",
                    "操作": "调仓",
                    "标的": "加仓白酒、减仓医药",
                    "理由": "消费复苏确定性高于医药政策风险",
                    "信心度": 0.70
                }
            ],
            "热门赛道共识": {
                "中证人工智能": {"看多": 8, "看空": 2, "共识": "强烈看多", "关键词": ["AI应用爆发", "算力需求", "大模型商业化"]},
                "中证半导体": {"看多": 7, "看空": 3, "共识": "看多", "关键词": ["周期见底", "国产替代", "设备材料"]},
                "中证医疗": {"看多": 6, "看空": 4, "共识": "中性偏多", "关键词": ["估值修复", "创新药", "集采常态化"]},
                "中证白酒": {"看多": 5, "看空": 5, "共识": "中性", "关键词": ["库存去化", "春节动销", "消费升级放缓"]},
                "中证新能源": {"看多": 4, "看空": 6, "共识": "中性偏空", "关键词": ["产能过剩", "价格战", "出海逻辑"]},
            }
        }
    
    def get_sector_heat(self, sector_name: str) -> Dict:
        """
        获取赛道热度分析
        
        Args:
            sector_name: 赛道名称
            
        Returns:
            热度数据
        """
        # 赛道热度评分 (模拟数据，实际可接入微博、雪球等舆情数据)
        sector_heat_map = {
            "中证白酒": {
                "heat_score": 65,
                "trend": "stable",
                "keywords": ["消费复苏", "库存去化", "春节预期"],
                "sentiment": "中性偏多"
            },
            "中证医疗": {
                "heat_score": 45,
                "trend": "down",
                "keywords": ["集采影响", "创新药", "估值修复"],
                "sentiment": "偏空"
            },
            "中证新能源": {
                "heat_score": 55,
                "trend": "up",
                "keywords": ["产能过剩", "出海", "储能"],
                "sentiment": "中性"
            },
            "中证半导体": {
                "heat_score": 75,
                "trend": "up",
                "keywords": ["国产替代", "AI芯片", "周期底部"],
                "sentiment": "偏多"
            },
            "中证军工": {
                "heat_score": 60,
                "trend": "stable",
                "keywords": ["十四五", "订单", "改革"],
                "sentiment": "中性"
            },
            "中证银行": {
                "heat_score": 50,
                "trend": "stable",
                "keywords": ["息差", "地产风险", "高股息"],
                "sentiment": "中性"
            },
            "证券公司": {
                "heat_score": 70,
                "trend": "up",
                "keywords": ["政策利好", "成交量", "并购"],
                "sentiment": "偏多"
            },
            "中证房地产": {
                "heat_score": 40,
                "trend": "down",
                "keywords": ["政策放松", "销售数据", "债务"],
                "sentiment": "偏空"
            },
            "中证人工智能": {
                "heat_score": 85,
                "trend": "up",
                "keywords": ["ChatGPT", "大模型", "算力"],
                "sentiment": "强烈看多"
            },
            "中证传媒": {
                "heat_score": 70,
                "trend": "up",
                "keywords": ["短剧", "游戏", "AI应用"],
                "sentiment": "偏多"
            },
            "沪深300": {
                "heat_score": 55,
                "trend": "stable",
                "keywords": ["核心资产", "估值低位", "北向资金"],
                "sentiment": "中性"
            },
            "中证500": {
                "heat_score": 60,
                "trend": "stable",
                "keywords": ["中小盘", "成长", "专精特新"],
                "sentiment": "中性偏多"
            },
            "创业板指": {
                "heat_score": 50,
                "trend": "down",
                "keywords": ["新能源", "医药", "估值"],
                "sentiment": "中性偏空"
            },
            "科创50": {
                "heat_score": 65,
                "trend": "up",
                "keywords": ["硬科技", "半导体", "创新"],
                "sentiment": "偏多"
            },
        }
        
        return sector_heat_map.get(sector_name, {
            "heat_score": 50,
            "trend": "stable",
            "keywords": [],
            "sentiment": "中性"
        })
    
    def get_blogger_opinions(self, fund_name: str) -> List[ResearchInsight]:
        """
        获取基金博主观点
        
        Args:
            fund_name: 基金名称
            
        Returns:
            观点列表
        """
        # 模拟博主观点数据
        opinions = []
        
        opinion_db = {
            "沪深300": [
                {
                    "source": "银行螺丝钉",
                    "author": "银行螺丝钉",
                    "content": "沪深300当前PE处于历史10%分位点以下，估值具有吸引力，适合定投。",
                    "sentiment": "bullish",
                    "date": "2024-01-10",
                    "relevance": 0.95
                },
                {
                    "source": "ETF拯救世界",
                    "author": "E大",
                    "content": "大盘蓝筹估值修复需要时间，但当前位置风险收益比已经不错。",
                    "sentiment": "bullish",
                    "date": "2024-01-08",
                    "relevance": 0.90
                }
            ],
            "中证医疗": [
                {
                    "source": "望京博格",
                    "author": "望京博格",
                    "content": "医疗板块受集采影响持续调整，但长期需求确定，当前可以开始关注。",
                    "sentiment": "neutral",
                    "date": "2024-01-12",
                    "relevance": 0.92
                }
            ],
            "中证半导体": [
                {
                    "source": "老罗话指数投资",
                    "author": "老罗",
                    "content": "半导体周期底部已现，国产替代加速，2024年有望迎来业绩修复。",
                    "sentiment": "bullish",
                    "date": "2024-01-15",
                    "relevance": 0.88
                }
            ],
            "中证白酒": [
                {
                    "source": "持有封基",
                    "author": "持有封基",
                    "content": "白酒板块库存去化需要时间，短期谨慎，但龙头长期配置价值仍在。",
                    "sentiment": "neutral",
                    "date": "2024-01-11",
                    "relevance": 0.85
                }
            ],
            "中证人工智能": [
                {
                    "source": "华夏基金",
                    "author": "华夏基金研究部",
                    "content": "AI产业链景气度高，算力、应用端都有机会，但需注意短期涨幅过大风险。",
                    "sentiment": "bullish",
                    "date": "2024-01-14",
                    "relevance": 0.90
                }
            ]
        }
        
        for op in opinion_db.get(fund_name, []):
            opinions.append(ResearchInsight(**op))
        
        return opinions
    
    def get_institutional_report(self, fund_name: str) -> Optional[ResearchInsight]:
        """
        获取机构研报观点
        
        Args:
            fund_name: 基金名称
            
        Returns:
            机构观点
        """
        # 模拟机构研报数据
        reports = {
            "沪深300": {
                "source": "中金公司",
                "author": "中金策略",
                "content": "维持对A股市场的积极看法，沪深300估值处于历史低位，建议超配。",
                "sentiment": "bullish",
                "date": "2024-01-15",
                "relevance": 0.95
            },
            "中证医疗": {
                "source": "中信证券",
                "author": "中信医药",
                "content": "医药板块估值已反映悲观预期，创新药和器械龙头具备配置价值。",
                "sentiment": "bullish",
                "date": "2024-01-12",
                "relevance": 0.92
            },
            "中证半导体": {
                "source": "国泰君安",
                "author": "国君电子",
                "content": "半导体行业周期见底，国产替代加速，看好设备材料环节。",
                "sentiment": "bullish",
                "date": "2024-01-10",
                "relevance": 0.90
            }
        }
        
        report = reports.get(fund_name)
        if report:
            return ResearchInsight(**report)
        return None
    
    def analyze_fund_sentiment(self, fund_name: str) -> Dict:
        """
        综合分析基金市场情绪
        
        Args:
            fund_name: 基金名称
            
        Returns:
            情绪分析结果
        """
        # 获取赛道热度
        heat = self.get_sector_heat(fund_name)
        
        # 获取博主观点
        opinions = self.get_blogger_opinions(fund_name)
        
        # 获取机构观点
        report = self.get_institutional_report(fund_name)
        
        # 计算综合情绪
        sentiment_scores = {
            "强烈看多": 1.0,
            "偏多": 0.6,
            "中性偏多": 0.3,
            "中性": 0,
            "中性偏空": -0.3,
            "偏空": -0.6,
            "强烈看空": -1.0
        }
        
        total_score = sentiment_scores.get(heat['sentiment'], 0)
        count = 1
        
        for op in opinions:
            if op.sentiment == "bullish":
                total_score += 0.5
            elif op.sentiment == "bearish":
                total_score -= 0.5
            count += 1
        
        if report:
            if report.sentiment == "bullish":
                total_score += 0.8
            elif report.sentiment == "bearish":
                total_score -= 0.8
            count += 1
        
        avg_sentiment = total_score / count if count > 0 else 0
        
        # 生成情绪标签
        if avg_sentiment > 0.5:
            sentiment_label = "强烈看多"
        elif avg_sentiment > 0.2:
            sentiment_label = "偏多"
        elif avg_sentiment > -0.2:
            sentiment_label = "中性"
        elif avg_sentiment > -0.5:
            sentiment_label = "偏空"
        else:
            sentiment_label = "强烈看空"
        
        return {
            "fund_name": fund_name,
            "heat_score": heat['heat_score'],
            "heat_trend": heat['trend'],
            "keywords": heat['keywords'],
            "sentiment": sentiment_label,
            "sentiment_score": round(avg_sentiment, 2),
            "opinion_count": len(opinions),
            "has_institutional_report": report is not None,
            "latest_opinions": [
                {
                    "source": op.source,
                    "content": op.content[:50] + "..." if len(op.content) > 50 else op.content,
                    "sentiment": op.sentiment
                }
                for op in opinions[:2]
            ]
        }
    
    def get_buy_recommendation_summary(self, fund_name: str) -> Optional[str]:
        """
        获取买入建议摘要
        
        Args:
            fund_name: 基金名称
            
        Returns:
            建议摘要
        """
        sentiment = self.analyze_fund_sentiment(fund_name)
        
        if sentiment['sentiment_score'] < 0:
            return None
        
        parts = []
        
        # 赛道热度
        if sentiment['heat_score'] > 70:
            parts.append(f"赛道热度较高({sentiment['heat_score']}分)")
        
        # 关键词
        if sentiment['keywords']:
            parts.append(f"关注关键词: {', '.join(sentiment['keywords'][:3])}")
        
        # 观点支持
        if sentiment['opinion_count'] > 0:
            parts.append(f"有{sentiment['opinion_count']}位大V看好")
        
        if sentiment['has_institutional_report']:
            parts.append("获机构研报推荐")
        
        return "；".join(parts) if parts else None
    
    def get_big_player_consensus(self, fund_name: str) -> Dict:
        """
        获取基金大佬对该基金的共识
        
        Args:
            fund_name: 基金名称
            
        Returns:
            大佬共识数据
        """
        # 查找与该基金相关的大佬动态
        related_insights = []
        consensus_data = self.latest_insights.get("热门赛道共识", {}).get(fund_name, {})
        
        for insight in self.latest_insights.get("大佬动态", []):
            if fund_name in insight.get("标的", ""):
                related_insights.append(insight)
        
        # 计算看多/看空比例
        if consensus_data:
            bullish = consensus_data.get("看多", 0)
            bearish = consensus_data.get("看空", 0)
            total = bullish + bearish
            bullish_ratio = bullish / total if total > 0 else 0.5
        else:
            bullish_ratio = 0.5
        
        return {
            "fund_name": fund_name,
            "consensus": consensus_data.get("共识", "中性"),
            "bullish_ratio": round(bullish_ratio, 2),
            "keywords": consensus_data.get("关键词", []),
            "big_player_actions": related_insights,
            "update_date": self.latest_insights.get("日期", "")
        }


if __name__ == "__main__":
    # 测试调研功能
    research = FundResearch()
    
    # 测试赛道热度
    print("=" * 60)
    print("赛道热度分析")
    print("=" * 60)
    
    sectors = ["沪深300", "中证医疗", "中证半导体", "中证人工智能", "中证白酒"]
    for sector in sectors:
        heat = research.get_sector_heat(sector)
        print(f"\n{sector}:")
        print(f"  热度分: {heat['heat_score']}")
        print(f"  趋势: {heat['trend']}")
        print(f"  情绪: {heat['sentiment']}")
        print(f"  关键词: {', '.join(heat['keywords'])}")
    
    # 测试情绪分析
    print("\n" + "=" * 60)
    print("基金情绪分析")
    print("=" * 60)
    
    for sector in ["沪深300", "中证医疗", "中证半导体"]:
        sentiment = research.analyze_fund_sentiment(sector)
        print(f"\n{sector}:")
        print(f"  综合情绪: {sentiment['sentiment']} ({sentiment['sentiment_score']})")
        print(f"  热度分: {sentiment['heat_score']}")
        print(f"  大V观点数: {sentiment['opinion_count']}")
        print(f"  机构研报: {'有' if sentiment['has_institutional_report'] else '无'}")
        
        summary = research.get_buy_recommendation_summary(sector)
        if summary:
            print(f"  买入建议: {summary}")
