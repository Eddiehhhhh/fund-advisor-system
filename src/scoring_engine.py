"""
基金评分引擎
多因子评分模型，综合估值、技术、资金、基本面、情绪等维度
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FundScore:
    """基金评分类"""
    fund_code: str
    fund_name: str
    total_score: float
    valuation_score: float
    technical_score: float
    fund_flow_score: float
    fundamental_score: float
    sentiment_score: float
    recommendation: str
    position_suggestion: str
    reasons: List[str]
    risks: List[str]


class ScoringEngine:
    """基金评分引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config['analysis']['weights']
        self.valuation_thresholds = config['analysis']['valuation']
    
    def calculate_valuation_score(self, pe_percentile: float, pb_percentile: float) -> Tuple[float, List[str]]:
        """
        计算估值评分
        
        评分逻辑:
        - PE/PB分位点越低，评分越高
        - 极度低估(<5%): 90-100分
        - 低估(5-20%): 75-90分
        - 合理(20-50%): 50-75分
        - 高估(50-80%): 25-50分
        - 极度高估(>80%): 0-25分
        """
        avg_percentile = (pe_percentile + pb_percentile) / 2
        reasons = []
        
        if avg_percentile < self.valuation_thresholds['extremely_low']:
            score = 95 - avg_percentile
            reasons.append(f"极度低估 (PE分位{pe_percentile:.1f}%, PB分位{pb_percentile:.1f}%)")
        elif avg_percentile < self.valuation_thresholds['low']:
            score = 85 - (avg_percentile - 5) * 0.67
            reasons.append(f"低估区间 (PE分位{pe_percentile:.1f}%, PB分位{pb_percentile:.1f}%)")
        elif avg_percentile < self.valuation_thresholds['normal']:
            score = 75 - (avg_percentile - 20) * 0.71
            reasons.append(f"估值合理偏低 (PE分位{pe_percentile:.1f}%)")
        elif avg_percentile < self.valuation_thresholds['high']:
            score = 50 - (avg_percentile - 50) * 0.83
            reasons.append(f"估值合理偏高 (PE分位{pe_percentile:.1f}%)")
        else:
            score = 25 - (avg_percentile - 80) * 0.83
            reasons.append(f"高估区间，建议观望")
        
        return max(0, min(100, score)), reasons
    
    def calculate_technical_score(self, indicators: Dict) -> Tuple[float, List[str]]:
        """
        计算技术面评分
        
        评分维度:
        - RSI (20%): 超卖加分，超买减分
        - MACD (25%): 金叉加分，死叉减分
        - 布林带 (25%): 触及下轨加分，触及上轨减分
        - 均线排列 (20%): 多头排列加分
        - 趋势 (10%): 上升趋势加分
        """
        score = 50  # 基础分
        reasons = []
        
        # RSI评分
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            score += 15
            reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi < 40:
            score += 8
            reasons.append(f"RSI接近超卖({rsi:.1f})")
        elif rsi > 70:
            score -= 15
            reasons.append(f"RSI超买({rsi:.1f})")
        elif rsi > 60:
            score -= 8
        
        # MACD评分
        macd_hist = indicators.get('macd_hist', 0)
        if macd_hist > 0:
            score += 12
            reasons.append("MACD金叉信号")
        else:
            score -= 8
        
        # 布林带评分
        price_position = indicators.get('price_position', 0.5)
        if price_position < 0.1:
            score += 15
            reasons.append("价格触及布林带下轨")
        elif price_position < 0.3:
            score += 8
            reasons.append("价格接近布林带下轨")
        elif price_position > 0.9:
            score -= 15
        
        # 均线评分
        ma_20 = indicators.get('ma_20', 0)
        ma_60 = indicators.get('ma_60', 0)
        if ma_20 > ma_60 * 1.02:
            score += 10
            reasons.append("短期均线上穿长期均线")
        elif ma_20 < ma_60 * 0.98:
            score -= 10
        
        # 趋势评分
        trend = indicators.get('trend_direction', 'sideways')
        if trend == 'up':
            score += 5
        elif trend == 'down':
            score -= 5
        
        return max(0, min(100, score)), reasons
    
    def calculate_fund_flow_score(self, flow_data: Dict) -> Tuple[float, List[str]]:
        """
        计算资金流向评分
        
        评分维度:
        - 北向资金流向 (40%)
        - 主力资金流向 (40%)
        - 成交量变化 (20%)
        """
        score = 50
        reasons = []
        
        # 北向资金
        north_money = flow_data.get('north_money_flow', 0)
        if north_money > 50:
            score += 20
            reasons.append(f"北向资金大幅流入({north_money:.1f}亿)")
        elif north_money > 20:
            score += 12
            reasons.append(f"北向资金流入({north_money:.1f}亿)")
        elif north_money < -50:
            score -= 20
        elif north_money < -20:
            score -= 12
        
        # 主力资金 (如果有数据)
        main_flow = flow_data.get('main_money_flow', 0)
        if main_flow > 0:
            score += 10
            reasons.append("主力资金净流入")
        
        return max(0, min(100, score)), reasons
    
    def calculate_fundamental_score(self, fund_info: Dict) -> Tuple[float, List[str]]:
        """
        计算基本面评分
        
        评分维度:
        - 基金规模 (25%): 适中规模为佳
        - 费率 (25%): 越低越好
        - 跟踪误差 (25%): 越小越好
        - 成立时间 (15%): 越长越好
        - 基金经理 (10%): 经验越丰富越好
        """
        score = 60  # 基础分
        reasons = []
        
        # 规模评分 (10-100亿为佳)
        scale = fund_info.get('scale', 50)
        if 10 <= scale <= 100:
            score += 15
            reasons.append(f"规模适中({scale:.1f}亿)")
        elif scale > 200:
            score -= 5
        elif scale < 2:
            score -= 10
        
        # 费率评分
        fee = fund_info.get('management_fee', 1.0)
        if fee < 0.3:
            score += 15
            reasons.append(f"管理费率低({fee}%)")
        elif fee < 0.5:
            score += 10
        elif fee > 1.0:
            score -= 10
        
        # 跟踪误差
        tracking_error = fund_info.get('tracking_error', 0.2)
        if tracking_error < 0.15:
            score += 15
            reasons.append(f"跟踪误差小({tracking_error}%)")
        elif tracking_error > 0.3:
            score -= 10
        
        # 成立时间
        establish_year = fund_info.get('establish_year', 5)
        if establish_year > 5:
            score += 10
            reasons.append("基金成立时间较长")
        
        return max(0, min(100, score)), reasons
    
    def calculate_sentiment_score(self, sentiment_data: Dict) -> Tuple[float, List[str]]:
        """
        计算市场情绪评分
        
        评分维度:
        - 市场整体涨跌比 (40%)
        - 恐慌/贪婪指数 (40%)
        - 波动率 (20%)
        """
        score = 50
        reasons = []
        
        # 涨跌家数比
        up_count = sentiment_data.get('up_count', 2000)
        if up_count > 3000:
            score += 15
            reasons.append("市场情绪较好")
        elif up_count < 1000:
            score -= 15
            reasons.append("市场情绪较差")
        
        # 恐慌贪婪指数 (0-100，50为中性)
        fear_greed = sentiment_data.get('fear_greed_index', 50)
        if fear_greed < 20:  # 极度恐慌
            score += 20
            reasons.append("市场极度恐慌，可能是买入时机")
        elif fear_greed < 40:  # 恐慌
            score += 10
        elif fear_greed > 80:  # 极度贪婪
            score -= 20
        
        return max(0, min(100, score)), reasons
    
    def calculate_total_score(self, 
                            fund_code: str,
                            fund_name: str,
                            valuation_data: Dict,
                            technical_indicators: Dict,
                            fund_flow_data: Dict,
                            fundamental_data: Dict,
                            sentiment_data: Dict) -> FundScore:
        """
        计算综合评分
        """
        # 各维度评分
        val_score, val_reasons = self.calculate_valuation_score(
            valuation_data.get('pe_percentile', 50),
            valuation_data.get('pb_percentile', 50)
        )
        
        tech_score, tech_reasons = self.calculate_technical_score(technical_indicators)
        flow_score, flow_reasons = self.calculate_fund_flow_score(fund_flow_data)
        fund_score, fund_reasons = self.calculate_fundamental_score(fundamental_data)
        sent_score, sent_reasons = self.calculate_sentiment_score(sentiment_data)
        
        # 加权总分
        total = (
            val_score * self.weights['valuation'] +
            tech_score * self.weights['technical'] +
            flow_score * self.weights['fund_flow'] +
            fund_score * self.weights['fundamental'] +
            sent_score * self.weights['sentiment']
        )
        
        # 生成建议
        recommendation, position = self._generate_recommendation(total, val_score, tech_score)
        
        # 汇总理由
        all_reasons = val_reasons + tech_reasons + flow_reasons + fund_reasons + sent_reasons
        
        # 风险提示
        risks = self._generate_risks(val_score, tech_score, technical_indicators)
        
        return FundScore(
            fund_code=fund_code,
            fund_name=fund_name,
            total_score=round(total, 1),
            valuation_score=round(val_score, 1),
            technical_score=round(tech_score, 1),
            fund_flow_score=round(flow_score, 1),
            fundamental_score=round(fund_score, 1),
            sentiment_score=round(sent_score, 1),
            recommendation=recommendation,
            position_suggestion=position,
            reasons=all_reasons[:5],  # 取前5个理由
            risks=risks
        )
    
    def _generate_recommendation(self, total_score: float, 
                                  val_score: float, 
                                  tech_score: float) -> Tuple[str, str]:
        """生成投资建议"""
        if total_score >= 80:
            if val_score >= 80 and tech_score >= 70:
                return "强烈建议买入", "可建仓30-50%"
            else:
                return "建议买入", "可建仓20-30%"
        elif total_score >= 65:
            return "可以关注", "可小仓位试探10-20%"
        elif total_score >= 50:
            return "中性观望", "保持关注，等待更好时机"
        elif total_score >= 35:
            return "建议观望", "暂不买入"
        else:
            return "建议回避", "避免买入"
    
    def _generate_risks(self, val_score: float, tech_score: float, indicators: Dict) -> List[str]:
        """生成风险提示"""
        risks = []
        
        if val_score > 70:
            risks.append("估值偏高，注意回调风险")
        
        volatility = indicators.get('volatility', 0.2)
        if volatility > 0.3:
            risks.append(f"波动率较高({volatility:.1%})，注意控制风险")
        
        rsi = indicators.get('rsi', 50)
        if rsi > 70:
            risks.append("技术指标显示超买")
        
        trend = indicators.get('trend_direction', 'sideways')
        if trend == 'down':
            risks.append("当前处于下降趋势")
        
        return risks if risks else ["暂无重大风险"]


if __name__ == "__main__":
    # 测试评分引擎
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
    
    engine = ScoringEngine(config)
    
    # 模拟数据
    score = engine.calculate_total_score(
        fund_code="000300",
        fund_name="沪深300",
        valuation_data={'pe_percentile': 8.5, 'pb_percentile': 5.2},
        technical_indicators={'rsi': 32, 'macd_hist': 0.5, 'price_position': 0.15, 
                             'ma_20': 3800, 'ma_60': 3850, 'trend_direction': 'sideways',
                             'volatility': 0.18},
        fund_flow_data={'north_money_flow': 35.5},
        fundamental_data={'scale': 45, 'management_fee': 0.5, 'tracking_error': 0.15, 'establish_year': 8},
        sentiment_data={'up_count': 2500, 'fear_greed_index': 35}
    )
    
    print(f"基金: {score.fund_name} ({score.fund_code})")
    print(f"总评分: {score.total_score}")
    print(f"估值评分: {score.valuation_score}")
    print(f"技术评分: {score.technical_score}")
    print(f"资金评分: {score.fund_flow_score}")
    print(f"基本面评分: {score.fundamental_score}")
    print(f"情绪评分: {score.sentiment_score}")
    print(f"建议: {score.recommendation}")
    print(f"仓位建议: {score.position_suggestion}")
    print(f"理由: {score.reasons}")
    print(f"风险: {score.risks}")
