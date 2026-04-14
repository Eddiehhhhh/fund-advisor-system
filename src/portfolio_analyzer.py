"""
持仓分析模块
多维度综合评估持仓基金，给出个性化建议
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
    from .news_analyzer import FundNewsAnalyzer, SentimentAnalysis
except ImportError:
    from data_fetcher import FundDataFetcher
    from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer, TrendAnalysis, TradingPoints
    from scoring_engine import ScoringEngine, FundScore
    from news_analyzer import FundNewsAnalyzer, SentimentAnalysis


@dataclass
class PositionAnalysis:
    """持仓基金分析结果"""
    fund_name: str
    fund_code: str
    position_amount: float  # 持仓金额
    position_ratio: float   # 占持仓比例
    current_return: float   # 当前收益率
    
    # 多维度评分
    total_score: float
    valuation_score: float
    technical_score: float
    sentiment_score: float
    trend_score: float
    
    # 估值分析
    pe_percentile: float
    valuation_status: str  # 极度低估/低估/合理/高估
    
    # 技术分析
    trend: TrendAnalysis
    trading_points: TradingPoints
    
    # 新闻舆情
    news_sentiment: SentimentAnalysis
    
    # 综合建议
    action: str  # 加仓/持有/减仓/止损/观望
    action_reason: str
    priority: int  # 优先级 1-5
    
    # 操作建议
    suggested_operation: str
    risk_level: str  # low/medium/high


@dataclass
class PortfolioSummary:
    """持仓组合汇总"""
    total_value: float
    total_return: float
    total_return_pct: float
    
    # 分布分析
    sector_distribution: Dict[str, float]  # 行业分布
    profit_loss_distribution: Dict[str, float]  # 盈亏分布
    
    # 风险分析
    concentration_risk: str  # 集中度风险
    correlation_risk: str    # 相关性风险
    
    # 整体建议
    overall_strategy: str
    rebalancing_suggestions: List[str]


class PortfolioAnalyzer:
    """持仓分析器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_fetcher = FundDataFetcher()
        self.tech_analyzer = EnhancedTechnicalAnalyzer()
        self.scoring_engine = ScoringEngine(config)
        self.news_analyzer = FundNewsAnalyzer()
        
        # 持仓映射（你的持仓基金名称 -> 指数代码）
        self.position_mapping = {
            "易方达恒生科技ETF联接(QDII)A": {"code": "HSI", "sector": "海外-港股", "type": "overseas"},
            "华夏有色金属ETF联接C": {"code": "000300", "sector": "周期-有色", "type": "sector"},  # 用沪深300近似
            "易方达人工智能ETF联接C": {"code": "930050", "sector": "科技-AI", "type": "sector"},
            "永赢先锋半导体智选混合C": {"code": "H30184", "sector": "科技-半导体", "type": "sector"},
            "招商中证白酒指数C": {"code": "399997", "sector": "消费-白酒", "type": "sector"},
            "平安鑫安混合E": {"code": "000300", "sector": "混合", "type": "broad_based"},
            "易方达全球成长精选混合(QDII)C": {"code": "NDX", "sector": "海外-全球", "type": "overseas"},
            "招商纳斯达克100ETF联接(QDII)A": {"code": "NDX", "sector": "海外-美股", "type": "overseas"},
            "建信新兴市场优选混合(QDII)C": {"code": "HSI", "sector": "海外-新兴", "type": "overseas"},
            "招商纳斯达克100ETF联接(QDII)C": {"code": "NDX", "sector": "海外-美股", "type": "overseas"},
            "广发中证建筑材料指数C": {"code": "931775", "sector": "周期-建材", "type": "sector"},
            "广发纳斯达克100ETF联接(QDII)A": {"code": "NDX", "sector": "海外-美股", "type": "overseas"},
            "华泰柏瑞质量成长混合C": {"code": "000300", "sector": "混合", "type": "broad_based"},
        }
    
    def analyze_portfolio(self, positions: List[Dict]) -> Tuple[List[PositionAnalysis], PortfolioSummary]:
        """
        分析整个持仓组合
        
        Args:
            positions: 持仓列表，每项包含 fund_name, amount, return_pct
        """
        total_value = sum(p['amount'] for p in positions)
        
        # 分析每只基金
        analyses = []
        for pos in positions:
            analysis = self._analyze_single_position(pos, total_value)
            if analysis:
                analyses.append(analysis)
        
        # 生成组合汇总
        summary = self._generate_portfolio_summary(analyses, total_value)
        
        return analyses, summary
    
    def _analyze_single_position(self, position: Dict, total_value: float) -> Optional[PositionAnalysis]:
        """
        分析单只持仓基金
        """
        fund_name = position['fund_name']
        amount = position['amount']
        return_pct = position['return_pct']
        
        # 查找映射
        mapping = self.position_mapping.get(fund_name)
        if not mapping:
            print(f"  未找到基金映射: {fund_name}")
            return None
        
        fund_code = mapping['code']
        
        print(f"  分析 {fund_name}...")
        
        try:
            # 1. 获取历史数据
            df = self.data_fetcher.get_fund_history(fund_code, days=120)
            if df.empty:
                print(f"    获取历史数据失败")
                return None
            
            # 2. 获取估值数据
            valuation = self.data_fetcher.get_index_valuation(fund_code)
            pe_percentile = valuation.get('pe_percentile', 50)
            
            # 3. 技术分析
            trend = self.tech_analyzer.analyze_trend(df)
            trading_points = self.tech_analyzer.calculate_trading_points(
                df, trend, pe_percentile
            )
            
            # 4. 评分计算
            fund_info = self.data_fetcher.get_fund_basic_info(fund_code)
            sentiment_data = self.data_fetcher.get_market_sentiment()
            
            # 简化技术指标
            tech_indicators = {
                'rsi': 50,  # 简化处理
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
            
            # 5. 新闻舆情
            news_sentiment = self.news_analyzer.analyze_fund_sentiment(mapping['sector'].split('-')[0])
            
            # 6. 综合决策
            action, action_reason, priority = self._make_decision(
                fund_name, amount, return_pct, score, trend, 
                pe_percentile, news_sentiment, total_value
            )
            
            # 7. 生成操作建议
            suggested_operation = self._generate_operation_suggestion(
                action, trading_points, trend
            )
            
            # 8. 风险评估
            risk_level = self._assess_risk(trend, pe_percentile, return_pct)
            
            return PositionAnalysis(
                fund_name=fund_name,
                fund_code=fund_code,
                position_amount=amount,
                position_ratio=round(amount / total_value * 100, 2),
                current_return=return_pct,
                total_score=score.total_score,
                valuation_score=score.valuation_score,
                technical_score=score.technical_score,
                sentiment_score=score.sentiment_score,
                trend_score=trend.trend_strength,
                pe_percentile=pe_percentile,
                valuation_status=self._get_valuation_status(pe_percentile),
                trend=trend,
                trading_points=trading_points,
                news_sentiment=news_sentiment,
                action=action,
                action_reason=action_reason,
                priority=priority,
                suggested_operation=suggested_operation,
                risk_level=risk_level
            )
            
        except Exception as e:
            print(f"    分析失败: {e}")
            return None
    
    def _make_decision(self, fund_name: str, amount: float, return_pct: float,
                       score: FundScore, trend: TrendAnalysis,
                       pe_percentile: float, news_sentiment: SentimentAnalysis,
                       total_value: float) -> Tuple[str, str, int]:
        """
        做出投资决策
        
        决策逻辑（多维度综合）：
        1. 如果估值极低(<20%) + 趋势良好 + 亏损较大 → 加仓摊薄
        2. 如果估值极高(>80%) + 盈利较好 + 趋势转弱 → 减仓
        3. 如果趋势多头排列 + 回调到支撑位 → 加仓
        4. 如果趋势空头排列 + 跌破支撑 → 止损
        5. 其他情况 → 持有观望
        """
        position_ratio = amount / total_value * 100
        
        # 高优先级：极端情况
        if return_pct < -15 and pe_percentile < 25 and trend.trend_direction in ["up", "strong_up"]:
            return "加仓", f"深度亏损({return_pct:.1f}%)但估值处于历史低位({pe_percentile:.1f}%)且趋势向上，建议加仓摊薄成本", 1
        
        if return_pct > 15 and pe_percentile > 75 and trend.trend_direction in ["down", "strong_down"]:
            return "减仓", f"盈利较好({return_pct:.1f}%)但估值偏高({pe_percentile:.1f}%)且趋势转弱，建议止盈减仓", 2
        
        # 中优先级：趋势信号
        if trend.is_bullish_alignment and trend.is_pullback and trend.pullback_to_ma in ["MA10", "MA20"]:
            if position_ratio < 20:  # 仓位不重
                return "加仓", f"多头排列回调至{trend.pullback_to_ma}，技术面买入信号，建议加仓", 3
        
        if trend.trend_direction in ["strong_down", "down"] and return_pct < -10:
            return "止损", f"趋势向下且亏损超10%，建议止损或减仓", 1
        
        # 低优先级：估值调整
        if pe_percentile < 15 and score.total_score > 65:
            return "加仓", f"估值极度低估({pe_percentile:.1f}%)，综合评分较高，建议逐步加仓", 4
        
        if pe_percentile > 85:
            return "减仓", f"估值偏高({pe_percentile:.1f}%)，建议减仓观望", 4
        
        # 默认：持有
        if return_pct < -5:
            return "持有", f"轻度亏损，等待反弹机会", 5
        elif return_pct > 5:
            return "持有", f"盈利中，可继续持有", 5
        else:
            return "观望", f"波动不大，建议观望", 5
    
    def _generate_operation_suggestion(self, action: str, 
                                       trading_points: TradingPoints,
                                       trend: TrendAnalysis) -> str:
        """生成具体操作建议"""
        if action == "加仓":
            if trading_points.entry_price > 0:
                return f"在{trading_points.entry_price:.4f}附近加仓，止损位{trading_points.stop_loss:.4f}，目标位{trading_points.take_profit_1:.4f}"
            else:
                return f"建议分批加仓，每次加当前持仓的20-30%"
        
        elif action == "减仓":
            return f"建议减仓30-50%，锁定部分利润"
        
        elif action == "止损":
            return f"建议止损，止损位参考{trading_points.stop_loss:.4f}或亏损10-15%"
        
        elif action == "持有":
            if trend.is_bullish_alignment:
                return f"继续持有，趋势良好，关注{trend.support_level:.4f}支撑位"
            else:
                return f"继续持有，等待趋势明朗"
        
        else:  # 观望
            return f"暂时观望，等待更好的入场时机"
    
    def _assess_risk(self, trend: TrendAnalysis, pe_percentile: float, 
                     return_pct: float) -> str:
        """评估风险等级"""
        risk_score = 0
        
        # 趋势风险
        if trend.trend_direction in ["strong_down", "down"]:
            risk_score += 3
        elif trend.trend_direction == "sideways":
            risk_score += 1
        
        # 估值风险
        if pe_percentile > 80:
            risk_score += 2
        elif pe_percentile < 20:
            risk_score -= 1
        
        # 亏损风险
        if return_pct < -15:
            risk_score += 2
        elif return_pct < -8:
            risk_score += 1
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _get_valuation_status(self, pe_percentile: float) -> str:
        """获取估值状态描述"""
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
    
    def _generate_portfolio_summary(self, analyses: List[PositionAnalysis], 
                                    total_value: float) -> PortfolioSummary:
        """生成持仓组合汇总"""
        
        # 计算总收益
        total_cost = sum(a.position_amount / (1 + a.current_return/100) for a in analyses)
        total_return = total_value - total_cost
        total_return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0
        
        # 行业分布
        sector_dist = {}
        for a in analyses:
            sector = self.position_mapping.get(a.fund_name, {}).get('sector', '其他')
            sector_dist[sector] = sector_dist.get(sector, 0) + a.position_amount
        
        # 归一化
        for sector in sector_dist:
            sector_dist[sector] = round(sector_dist[sector] / total_value * 100, 2)
        
        # 盈亏分布
        profit_amount = sum(a.position_amount * a.current_return / 100 
                           for a in analyses if a.current_return > 0)
        loss_amount = sum(a.position_amount * a.current_return / 100 
                         for a in analyses if a.current_return < 0)
        
        profit_loss_dist = {
            '盈利': round(profit_amount / total_value * 100, 2),
            '亏损': round(abs(loss_amount) / total_value * 100, 2),
            '持平': round(100 - abs(profit_amount / total_value * 100) - abs(loss_amount / total_value * 100), 2)
        }
        
        # 集中度风险
        max_ratio = max(a.position_ratio for a in analyses) if analyses else 0
        if max_ratio > 30:
            concentration_risk = "高集中度风险"
        elif max_ratio > 20:
            concentration_risk = "中等集中度"
        else:
            concentration_risk = "分散良好"
        
        # 相关性风险（简化版）
        overseas_count = sum(1 for a in analyses 
                           if self.position_mapping.get(a.fund_name, {}).get('type') == 'overseas')
        if overseas_count > 5:
            correlation_risk = "海外基金过于集中，注意汇率风险"
        else:
            correlation_risk = "相关性风险可控"
        
        # 整体策略
        avg_score = sum(a.total_score for a in analyses) / len(analyses) if analyses else 50
        if avg_score > 70:
            overall_strategy = "组合整体评分较高，可积极操作"
        elif avg_score > 50:
            overall_strategy = "组合表现中等，精选个股操作"
        else:
            overall_strategy = "组合评分偏低，建议优化结构"
        
        # 再平衡建议
        rebalancing = []
        
        # 检查是否有过高仓位的亏损基金
        for a in analyses:
            if a.position_ratio > 25 and a.current_return < -5:
                rebalancing.append(f"{a.fund_name}占比过高({a.position_ratio}%)且亏损，建议控制仓位")
        
        # 检查纳斯达克100重复
        ndx_count = sum(1 for a in analyses if '纳斯达克' in a.fund_name)
        if ndx_count > 1:
            rebalancing.append(f"纳斯达克100持有{ndx_count}只，建议合并简化")
        
        return PortfolioSummary(
            total_value=round(total_value, 2),
            total_return=round(total_return, 2),
            total_return_pct=round(total_return_pct, 2),
            sector_distribution=sector_dist,
            profit_loss_distribution=profit_loss_dist,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            overall_strategy=overall_strategy,
            rebalancing_suggestions=rebalancing
        )


if __name__ == "__main__":
    # 测试
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
    
    # 模拟持仓
    test_positions = [
        {'fund_name': '易方达恒生科技ETF联接(QDII)A', 'amount': 8832.94, 'return_pct': -8.25},
        {'fund_name': '易方达人工智能ETF联接C', 'amount': 5115.45, 'return_pct': 2.31},
        {'fund_name': '永赢先锋半导体智选混合C', 'amount': 3256.46, 'return_pct': 8.55},
    ]
    
    analyzer = PortfolioAnalyzer(config)
    analyses, summary = analyzer.analyze_portfolio(test_positions)
    
    print("\n" + "=" * 60)
    print("持仓分析结果")
    print("=" * 60)
    
    for a in analyses:
        print(f"\n{a.fund_name}")
        print(f"  持仓: ¥{a.position_amount} ({a.position_ratio}%)")
        print(f"  收益: {a.current_return}%")
        print(f"  评分: {a.total_score}")
        print(f"  估值: {a.valuation_status} ({a.pe_percentile}%)")
        print(f"  趋势: {a.trend.trend_direction} (强度{a.trend.trend_strength})")
        print(f"  建议: {a.action} - {a.action_reason}")
        print(f"  操作: {a.suggested_operation}")
