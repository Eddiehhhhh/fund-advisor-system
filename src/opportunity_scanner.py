"""
机会扫描模块
扫描所有基金，发现买入机会
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from .data_fetcher import FundDataFetcher
    from .enhanced_technical_analyzer import EnhancedTechnicalAnalyzer, TrendAnalysis, TradingPoints
    from .scoring_engine import ScoringEngine, FundScore
    from .news_analyzer import FundNewsAnalyzer
except ImportError:
    from data_fetcher import FundDataFetcher
    from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer, TrendAnalysis, TradingPoints
    from scoring_engine import ScoringEngine, FundScore
    from news_analyzer import FundNewsAnalyzer


@dataclass
class Opportunity:
    """投资机会"""
    fund_code: str
    fund_name: str
    fund_type: str  # 宽基/行业/海外
    
    # 评分
    total_score: float
    valuation_score: float
    technical_score: float
    trend_score: float
    
    # 估值
    pe_percentile: float
    valuation_status: str
    
    # 技术
    trend: TrendAnalysis
    trading_points: TradingPoints
    
    # 机会类型
    opportunity_type: str  # 估值修复/趋势突破/回调买入/超跌反弹
    opportunity_desc: str
    
    # 预期收益
    expected_return_1m: float  # 1个月预期收益
    expected_return_3m: float  # 3个月预期收益
    success_probability: float
    
    # 建议
    position_size: str  # light/medium/heavy
    urgency: str  # high/medium/low


class OpportunityScanner:
    """机会扫描器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_fetcher = FundDataFetcher()
        self.tech_analyzer = EnhancedTechnicalAnalyzer()
        self.scoring_engine = ScoringEngine(config)
        self.news_analyzer = FundNewsAnalyzer()
        
        # 基金池
        self.fund_pool = self._load_fund_pool()
    
    def _load_fund_pool(self) -> List[Dict]:
        """加载基金池"""
        return self.data_fetcher.get_fund_list()
    
    def scan_all_opportunities(self) -> List[Opportunity]:
        """
        扫描所有基金，找出投资机会
        """
        opportunities = []
        
        print("开始扫描基金机会...")
        
        for fund in self.fund_pool:
            fund_code = fund['code']
            fund_name = fund['name']
            fund_type = fund.get('type', 'unknown')
            
            try:
                opportunity = self._analyze_fund_opportunity(fund_code, fund_name, fund_type)
                if opportunity and self._is_good_opportunity(opportunity):
                    opportunities.append(opportunity)
                    print(f"  ✅ 发现机会: {fund_name} ({opportunity.opportunity_type})")
            except Exception as e:
                print(f"  ❌ 分析 {fund_name} 失败: {e}")
                continue
        
        # 按综合评分排序
        opportunities.sort(key=lambda x: x.total_score, reverse=True)
        
        return opportunities
    
    def _analyze_fund_opportunity(self, fund_code: str, fund_name: str, 
                                   fund_type: str) -> Optional[Opportunity]:
        """
        分析单只基金的投资机会
        """
        # 1. 获取数据
        df = self.data_fetcher.get_fund_history(fund_code, days=120)
        if df.empty or len(df) < 60:
            return None
        
        valuation = self.data_fetcher.get_index_valuation(fund_code)
        pe_percentile = valuation.get('pe_percentile', 50)
        
        # 2. 技术分析
        trend = self.tech_analyzer.analyze_trend(df)
        trading_points = self.tech_analyzer.calculate_trading_points(
            df, trend, pe_percentile
        )
        
        # 3. 评分
        fund_info = self.data_fetcher.get_fund_basic_info(fund_code)
        sentiment_data = self.data_fetcher.get_market_sentiment()
        
        tech_indicators = {
            'rsi': 50,
            'macd_hist': 0,
            'price_position': 0.5,
            'ma_20': trend.ma20,
            'ma_60': trend.ma60,
            'trend_direction': trend.trend_direction,
            'volatility': 0.2
        }
        
        score = self.scoring_engine.calculate_total_score(
            fund_code=fund_code,
            fund_name=fund_name,
            valuation_data=valuation,
            technical_indicators=tech_indicators,
            fund_flow_data=sentiment_data,
            fundamental_data=fund_info,
            sentiment_data=sentiment_data
        )
        
        # 4. 判断机会类型
        opportunity_type, opportunity_desc = self._identify_opportunity_type(
            trend, pe_percentile, score
        )
        
        if not opportunity_type:
            return None
        
        # 5. 计算预期收益
        expected_1m, expected_3m = self._estimate_returns(trend, pe_percentile, opportunity_type)
        
        # 6. 确定仓位和 urgency
        position_size = self._determine_position_size(trend, pe_percentile, score)
        urgency = self._determine_urgency(trend, opportunity_type)
        
        return Opportunity(
            fund_code=fund_code,
            fund_name=fund_name,
            fund_type=fund_type,
            total_score=score.total_score,
            valuation_score=score.valuation_score,
            technical_score=score.technical_score,
            trend_score=trend.trend_strength,
            pe_percentile=pe_percentile,
            valuation_status=self._get_valuation_status(pe_percentile),
            trend=trend,
            trading_points=trading_points,
            opportunity_type=opportunity_type,
            opportunity_desc=opportunity_desc,
            expected_return_1m=expected_1m,
            expected_return_3m=expected_3m,
            success_probability=trading_points.success_probability,
            position_size=position_size,
            urgency=urgency
        )
    
    def _identify_opportunity_type(self, trend: TrendAnalysis, 
                                    pe_percentile: float,
                                    score: FundScore) -> Tuple[Optional[str], str]:
        """
        识别机会类型
        
        Returns:
            (机会类型, 描述)
        """
        # 类型1: 多头排列回调买入（最高优先级）
        if trend.is_bullish_alignment and trend.is_pullback:
            if trend.pullback_to_ma in ["MA10", "MA20"]:
                return (
                    "回调买入",
                    f"多头排列，回调至{trend.pullback_to_ma}，趋势延续概率高"
                )
        
        # 类型2: 估值修复（低估值+趋势好转）
        if pe_percentile < 20 and score.total_score > 60:
            if trend.trend_direction in ["up", "sideways"]:
                return (
                    "估值修复",
                    f"估值处于历史低位({pe_percentile:.1f}%)，具备修复空间"
                )
        
        # 类型3: 趋势突破
        if trend.trend_direction == "up" and not trend.is_pullback:
            if trend.trend_strength > 60 and pe_percentile < 60:
                return (
                    "趋势突破",
                    f"强势上涨趋势，动能充足"
                )
        
        # 类型4: 超跌反弹
        if pe_percentile < 30 and trend.trend_direction == "down":
            if trend.buy_signals and "超跌反弹信号" in trend.buy_signals:
                return (
                    "超跌反弹",
                    f"深度回调后可能出现反弹"
                )
        
        return None, ""
    
    def _estimate_returns(self, trend: TrendAnalysis, pe_percentile: float,
                          opportunity_type: str) -> Tuple[float, float]:
        """
        估算预期收益
        """
        base_return_1m = 3  # 基础月收益3%
        base_return_3m = 8  # 基础季度收益8%
        
        # 趋势调整
        if trend.trend_direction == "strong_up":
            base_return_1m += 3
            base_return_3m += 8
        elif trend.trend_direction == "up":
            base_return_1m += 2
            base_return_3m += 5
        elif trend.trend_direction == "down":
            base_return_1m -= 2
            base_return_3m -= 3
        
        # 估值调整
        if pe_percentile < 10:
            base_return_1m += 2
            base_return_3m += 6
        elif pe_percentile < 25:
            base_return_1m += 1
            base_return_3m += 3
        elif pe_percentile > 80:
            base_return_1m -= 2
            base_return_3m -= 4
        
        # 机会类型调整
        adjustments = {
            "回调买入": (2, 5),
            "估值修复": (1, 4),
            "趋势突破": (3, 6),
            "超跌反弹": (2, 3)
        }
        
        adj = adjustments.get(opportunity_type, (0, 0))
        
        return round(base_return_1m + adj[0], 1), round(base_return_3m + adj[1], 1)
    
    def _determine_position_size(self, trend: TrendAnalysis, 
                                  pe_percentile: float,
                                  score: FundScore) -> str:
        """确定建议仓位"""
        score_factor = score.total_score / 100
        valuation_factor = (100 - pe_percentile) / 100
        trend_factor = trend.trend_strength / 100
        
        combined = (score_factor + valuation_factor + trend_factor) / 3
        
        if combined > 0.7:
            return "heavy"  # 重仓 30-50%
        elif combined > 0.5:
            return "medium"  # 中仓 15-25%
        else:
            return "light"  # 轻仓 5-10%
    
    def _determine_urgency(self, trend: TrendAnalysis, 
                           opportunity_type: str) -> str:
        """确定紧急程度"""
        if opportunity_type == "回调买入" and trend.is_pullback:
            return "high"  # 回调买入窗口期短
        
        if trend.trend_direction == "strong_up":
            return "medium"
        
        return "low"
    
    def _is_good_opportunity(self, opp: Opportunity) -> bool:
        """判断是否是好机会"""
        # 综合评分>65
        if opp.total_score < 65:
            return False
        
        # 成功率>50%
        if opp.success_probability < 50:
            return False
        
        # 1个月预期收益>5%
        if opp.expected_return_1m < 5:
            return False
        
        return True
    
    def _get_valuation_status(self, pe_percentile: float) -> str:
        """获取估值状态"""
        if pe_percentile < 5:
            return "极度低估"
        elif pe_percentile < 20:
            return "低估"
        elif pe_percentile < 50:
            return "合理偏低"
        elif pe_percentile < 80:
            return "合理偏高"
        else:
            return "高估"
    
    def get_top_opportunities(self, n: int = 5) -> List[Opportunity]:
        """获取前N个最佳机会"""
        all_opps = self.scan_all_opportunities()
        return all_opps[:n]
    
    def generate_opportunity_report(self, opportunities: List[Opportunity]) -> str:
        """生成机会报告"""
        if not opportunities:
            return "未发现明显投资机会，建议观望"
        
        lines = []
        lines.append("=" * 60)
        lines.append("🎯 投资机会推荐")
        lines.append("=" * 60)
        
        for i, opp in enumerate(opportunities[:5], 1):
            urgency_emoji = {"high": "🔥", "medium": "⭐", "low": "💡"}[opp.urgency]
            
            lines.append(f"\n{i}. {urgency_emoji} {opp.fund_name} ({opp.fund_type})")
            lines.append(f"   机会类型: {opp.opportunity_type}")
            lines.append(f"   机会描述: {opp.opportunity_desc}")
            lines.append(f"   综合评分: {opp.total_score:.1f} (估值{opp.valuation_score:.1f} 技术{opp.technical_score:.1f})")
            lines.append(f"   估值状态: {opp.valuation_status} (PE分位{opp.pe_percentile:.1f}%)")
            lines.append(f"   趋势方向: {opp.trend.trend_direction} (强度{opp.trend.trend_strength:.1f})")
            lines.append(f"   预期收益: 1个月+{opp.expected_return_1m}% | 3个月+{opp.expected_return_3m}%")
            lines.append(f"   成功率: {opp.success_probability:.0f}%")
            lines.append(f"   建议仓位: {opp.position_size} | 紧急度: {opp.urgency}")
            
            if opp.trading_points.entry_price > 0:
                lines.append(f"   买入点位: {opp.trading_points.entry_price:.4f}")
                lines.append(f"   止损点位: {opp.trading_points.stop_loss:.4f}")
                lines.append(f"   目标点位: {opp.trading_points.take_profit_1:.4f} / {opp.trading_points.take_profit_2:.4f}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    config = {
        'analysis': {
            'weights': {
                'valuation': 0.30,
                'technical': 0.25,
                'fund_flow': 0.20,
                'fundamental': 0.15,
                'sentiment': 0.10
            },
            'valuation': {
                'extremely_low': 5,
                'low': 20,
                'normal': 50,
                'high': 80
            }
        }
    }
    
    scanner = OpportunityScanner(config)
    opportunities = scanner.get_top_opportunities(5)
    
    print(scanner.generate_opportunity_report(opportunities))
