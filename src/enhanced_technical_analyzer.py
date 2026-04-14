"""
增强版技术分析模块
参考 daily_stock_analysis 项目，添加：
1. 多头排列检测
2. 回调买入信号
3. 精确买卖点计算
4. 趋势强度评估
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    trend_direction: str  # strong_up/up/sideways/down/strong_down
    trend_strength: float  # 0-100
    ma_alignment: str  # bullish_alignment/bearish_alignment/mixed
    is_bullish_alignment: bool  # 是否多头排列
    
    # 均线数据
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    ma120: float
    
    # 价格位置
    price_vs_ma5: float  # 价格相对MA5的百分比
    price_vs_ma20: float
    price_vs_ma60: float
    
    # 回调信息
    is_pullback: bool  # 是否处于回调中
    pullback_depth: float  # 回调深度（从近期高点）
    pullback_to_ma: str  # 回调到哪个均线支撑
    
    # 支撑阻力
    support_level: float
    resistance_level: float
    
    # 买入信号
    buy_signals: List[str]
    risk_signals: List[str]


@dataclass
class TradingPoints:
    """交易点位建议"""
    entry_price: float  # 建议买入价
    stop_loss: float    # 止损价
    take_profit_1: float  # 第一目标价
    take_profit_2: float  # 第二目标价
    take_profit_3: float  # 第三目标价
    
    entry_reason: str   # 买入理由
    stop_loss_reason: str  # 止损理由
    
    position_size: str  # 建议仓位: light/medium/heavy
    holding_period: str  # 建议持有周期: short/medium/long
    
    risk_reward_ratio: float  # 盈亏比
    success_probability: float  # 成功率估计


class EnhancedTechnicalAnalyzer:
    """增强版技术分析器"""
    
    def __init__(self):
        self.short_term = 5
        self.medium_term = 10
        self.long_term = 20
        self.trend_term = 60
        self.super_long = 120
    
    def calculate_all_ma(self, prices: pd.Series) -> Dict[str, float]:
        """计算所有均线"""
        return {
            'ma5': prices.rolling(window=5).mean().iloc[-1],
            'ma10': prices.rolling(window=10).mean().iloc[-1],
            'ma20': prices.rolling(window=20).mean().iloc[-1],
            'ma60': prices.rolling(window=60).mean().iloc[-1],
            'ma120': prices.rolling(window=120).mean().iloc[-1] if len(prices) >= 120 else prices.rolling(window=60).mean().iloc[-1],
        }
    
    def analyze_trend(self, df: pd.DataFrame) -> TrendAnalysis:
        """
        全面趋势分析
        """
        if len(df) < 60:
            return self._empty_trend_analysis()
        
        prices = df['nav']
        current_price = prices.iloc[-1]
        
        # 计算均线
        mas = self.calculate_all_ma(prices)
        ma5, ma10, ma20, ma60, ma120 = mas['ma5'], mas['ma10'], mas['ma20'], mas['ma60'], mas['ma120']
        
        # 判断多头排列
        is_bullish_alignment = (ma5 > ma10 > ma20 > ma60)
        is_bearish_alignment = (ma5 < ma10 < ma20 < ma60)
        
        if is_bullish_alignment:
            ma_alignment = "bullish_alignment"
        elif is_bearish_alignment:
            ma_alignment = "bearish_alignment"
        else:
            ma_alignment = "mixed"
        
        # 计算趋势强度
        trend_strength = self._calculate_trend_strength(prices, mas)
        
        # 判断趋势方向
        if is_bullish_alignment and trend_strength > 70:
            trend_direction = "strong_up"
        elif is_bullish_alignment or (ma20 > ma60 and trend_strength > 50):
            trend_direction = "up"
        elif is_bearish_alignment and trend_strength > 70:
            trend_direction = "strong_down"
        elif is_bearish_alignment or (ma20 < ma60 and trend_strength > 50):
            trend_direction = "down"
        else:
            trend_direction = "sideways"
        
        # 计算价格相对均线位置
        price_vs_ma5 = (current_price - ma5) / ma5 * 100
        price_vs_ma20 = (current_price - ma20) / ma20 * 100
        price_vs_ma60 = (current_price - ma60) / ma60 * 100
        
        # 检测回调
        is_pullback, pullback_depth, pullback_to_ma = self._detect_pullback(
            prices, current_price, mas
        )
        
        # 计算支撑阻力
        support, resistance = self._calculate_support_resistance(prices)
        
        # 生成信号
        buy_signals = self._generate_buy_signals(
            current_price, mas, is_bullish_alignment, is_pullback, 
            pullback_to_ma, df
        )
        risk_signals = self._generate_risk_signals(
            current_price, mas, trend_direction, df
        )
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            ma_alignment=ma_alignment,
            is_bullish_alignment=is_bullish_alignment,
            ma5=round(ma5, 4),
            ma10=round(ma10, 4),
            ma20=round(ma20, 4),
            ma60=round(ma60, 4),
            ma120=round(ma120, 4),
            price_vs_ma5=round(price_vs_ma5, 2),
            price_vs_ma20=round(price_vs_ma20, 2),
            price_vs_ma60=round(price_vs_ma60, 2),
            is_pullback=is_pullback,
            pullback_depth=round(pullback_depth, 2),
            pullback_to_ma=pullback_to_ma,
            support_level=round(support, 4),
            resistance_level=round(resistance, 4),
            buy_signals=buy_signals,
            risk_signals=risk_signals
        )
    
    def _calculate_trend_strength(self, prices: pd.Series, mas: Dict) -> float:
        """计算趋势强度 0-100"""
        if len(prices) < 20:
            return 50
        
        # 基于均线斜率计算
        ma20_slope = (mas['ma20'] - prices.rolling(window=20).mean().iloc[-5]) / 5
        ma60_slope = (mas['ma60'] - prices.rolling(window=60).mean().iloc[-10]) / 10 if len(prices) >= 70 else 0
        
        # 价格相对于均线的位置
        price_position = (prices.iloc[-1] - mas['ma60']) / mas['ma60'] * 100
        
        # 近期涨跌幅
        recent_change = (prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20] * 100
        
        # 综合计算
        strength = 50
        if ma20_slope > 0:
            strength += min(20, ma20_slope * 10)
        else:
            strength -= min(20, abs(ma20_slope) * 10)
        
        if price_position > 0:
            strength += min(15, price_position * 2)
        else:
            strength -= min(15, abs(price_position) * 2)
        
        strength += min(15, recent_change)
        
        return max(0, min(100, strength))
    
    def _detect_pullback(self, prices: pd.Series, current_price: float, 
                         mas: Dict) -> Tuple[bool, float, str]:
        """
        检测是否处于回调中
        
        Returns:
            (是否回调, 回调深度, 回调到哪个均线)
        """
        if len(prices) < 20:
            return False, 0, ""
        
        # 找近期高点（最近20天）
        recent_high = prices.tail(20).max()
        recent_low = prices.tail(20).min()
        
        # 计算回调深度
        pullback_depth = (recent_high - current_price) / (recent_high - recent_low) * 100
        
        # 判断是否回调（从高点回落超过3%）
        is_pullback = (recent_high - current_price) / recent_high > 0.03
        
        # 判断回调到哪个均线
        pullback_to_ma = ""
        if current_price <= mas['ma5'] * 1.01 and current_price >= mas['ma5'] * 0.99:
            pullback_to_ma = "MA5"
        elif current_price <= mas['ma10'] * 1.01 and current_price >= mas['ma10'] * 0.99:
            pullback_to_ma = "MA10"
        elif current_price <= mas['ma20'] * 1.02 and current_price >= mas['ma20'] * 0.98:
            pullback_to_ma = "MA20"
        elif current_price <= mas['ma60'] * 1.03 and current_price >= mas['ma60'] * 0.97:
            pullback_to_ma = "MA60"
        
        return is_pullback, pullback_depth, pullback_to_ma
    
    def _calculate_support_resistance(self, prices: pd.Series) -> Tuple[float, float]:
        """计算支撑阻力位"""
        if len(prices) < 20:
            current = prices.iloc[-1]
            return current * 0.95, current * 1.05
        
        # 基于近期高低点
        recent_20 = prices.tail(20)
        support = recent_20.min()
        resistance = recent_20.max()
        
        # 基于成交量加权（如果有成交量数据）
        return support, resistance
    
    def _generate_buy_signals(self, current_price: float, mas: Dict,
                              is_bullish_alignment: bool, is_pullback: bool,
                              pullback_to_ma: str, df: pd.DataFrame) -> List[str]:
        """生成买入信号"""
        signals = []
        
        # 1. 多头排列回调买入（核心策略）
        if is_bullish_alignment and is_pullback and pullback_to_ma in ["MA10", "MA20"]:
            signals.append(f"🎯 多头排列回调至{pullback_to_ma}，趋势延续买入点")
        
        # 2. 均线金叉
        if mas['ma5'] > mas['ma10'] and mas['ma10'] > mas['ma20']:
            if mas['ma5'] > mas['ma10'] * 1.001:  # 确保是刚金叉
                signals.append("📈 短期均线金叉")
        
        # 3. 突破买入
        if current_price > mas['ma20'] * 1.02 and df['nav'].iloc[-2] <= mas['ma20']:
            signals.append("🚀 突破20日均线")
        
        # 4. 超跌反弹
        if len(df) >= 10:
            recent_change = (current_price - df['nav'].iloc[-10]) / df['nav'].iloc[-10] * 100
            if recent_change < -10 and current_price > df['nav'].iloc[-1]:
                signals.append("⬆️ 超跌反弹信号")
        
        # 5. 均线支撑
        if is_bullish_alignment and current_price > mas['ma20']:
            signals.append("✅ 均线多头排列支撑")
        
        return signals
    
    def _generate_risk_signals(self, current_price: float, mas: Dict,
                               trend_direction: str, df: pd.DataFrame) -> List[str]:
        """生成风险信号"""
        signals = []
        
        # 1. 趋势风险
        if trend_direction in ["strong_down", "down"]:
            signals.append("⚠️ 处于下降趋势")
        
        # 2. 跌破均线
        if current_price < mas['ma20'] and df['nav'].iloc[-2] >= mas['ma20']:
            signals.append("🚨 跌破20日均线")
        
        # 3. 均线死叉
        if mas['ma5'] < mas['ma10'] and mas['ma10'] < mas['ma20']:
            signals.append("📉 短期均线空头排列")
        
        # 4. 远离均线
        price_vs_ma20 = (current_price - mas['ma20']) / mas['ma20'] * 100
        if price_vs_ma20 > 15:
            signals.append(f"⚠️ 价格偏离均线过远(+{price_vs_ma20:.1f}%)，注意回调风险")
        
        return signals
    
    def calculate_trading_points(self, df: pd.DataFrame, 
                                  trend: TrendAnalysis,
                                  valuation_percentile: float = 50) -> TradingPoints:
        """
        计算精确交易点位
        """
        if df.empty or len(df) < 20:
            return self._empty_trading_points()
        
        current_price = df['nav'].iloc[-1]
        
        # 确定买入价
        if trend.is_pullback and trend.pullback_to_ma:
            # 回调买入：当前价或略低于当前价
            entry_price = current_price * 0.995
        elif trend.is_bullish_alignment:
            # 多头排列：回踩MA20买入
            entry_price = trend.ma20 * 1.01
        else:
            # 其他情况：当前价
            entry_price = current_price
        
        # 确定止损价（关键支撑位下方）
        if trend.is_bullish_alignment:
            stop_loss = min(trend.ma60 * 0.97, trend.support_level * 0.98)
        else:
            stop_loss = trend.support_level * 0.97
        
        # 确定目标价
        risk = entry_price - stop_loss
        
        # 基于估值分位调整目标
        if valuation_percentile < 20:  # 低估值
            take_profit_1 = entry_price + risk * 2  # 盈亏比 2:1
            take_profit_2 = entry_price + risk * 3
            take_profit_3 = entry_price + risk * 5
        elif valuation_percentile < 50:  # 合理估值
            take_profit_1 = entry_price + risk * 1.5
            take_profit_2 = entry_price + risk * 2.5
            take_profit_3 = entry_price + risk * 4
        else:  # 高估值
            take_profit_1 = entry_price + risk * 1
            take_profit_2 = entry_price + risk * 2
            take_profit_3 = entry_price + risk * 3
        
        # 建议仓位
        if trend.is_bullish_alignment and valuation_percentile < 30:
            position_size = "heavy"  # 重仓
        elif trend.is_bullish_alignment or valuation_percentile < 30:
            position_size = "medium"  # 中等
        else:
            position_size = "light"  # 轻仓
        
        # 建议持有周期
        if trend.trend_direction in ["strong_up", "up"]:
            holding_period = "medium"  # 1-3个月
        else:
            holding_period = "short"  # 1个月内
        
        # 盈亏比
        risk_reward = (take_profit_1 - entry_price) / (entry_price - stop_loss) if (entry_price - stop_loss) > 0 else 0
        
        # 成功率估计
        success_prob = self._estimate_success_probability(trend, valuation_percentile)
        
        return TradingPoints(
            entry_price=round(entry_price, 4),
            stop_loss=round(stop_loss, 4),
            take_profit_1=round(take_profit_1, 4),
            take_profit_2=round(take_profit_2, 4),
            take_profit_3=round(take_profit_3, 4),
            entry_reason=self._generate_entry_reason(trend),
            stop_loss_reason=f"跌破关键支撑位({trend.pullback_to_ma if trend.pullback_to_ma else '近期低点'})",
            position_size=position_size,
            holding_period=holding_period,
            risk_reward_ratio=round(risk_reward, 2),
            success_probability=round(success_prob, 2)
        )
    
    def _estimate_success_probability(self, trend: TrendAnalysis, 
                                       valuation_percentile: float) -> float:
        """估计交易成功率"""
        prob = 50  # 基础概率
        
        # 趋势加分
        if trend.trend_direction == "strong_up":
            prob += 15
        elif trend.trend_direction == "up":
            prob += 10
        
        # 多头排列加分
        if trend.is_bullish_alignment:
            prob += 10
        
        # 回调买入加分
        if trend.is_pullback and trend.pullback_to_ma:
            prob += 10
        
        # 估值加分
        if valuation_percentile < 20:
            prob += 10
        elif valuation_percentile < 40:
            prob += 5
        
        # 趋势强度加分
        prob += (trend.trend_strength - 50) / 5
        
        return max(30, min(90, prob))
    
    def _generate_entry_reason(self, trend: TrendAnalysis) -> str:
        """生成买入理由"""
        reasons = []
        
        if trend.is_bullish_alignment:
            reasons.append("多头排列")
        
        if trend.is_pullback:
            reasons.append(f"回调至{trend.pullback_to_ma}")
        
        if trend.trend_direction in ["strong_up", "up"]:
            reasons.append("上升趋势")
        
        return "，".join(reasons) if reasons else "技术形态良好"
    
    def _empty_trend_analysis(self) -> TrendAnalysis:
        """返回空的趋势分析"""
        return TrendAnalysis(
            trend_direction="unknown",
            trend_strength=50,
            ma_alignment="unknown",
            is_bullish_alignment=False,
            ma5=0, ma10=0, ma20=0, ma60=0, ma120=0,
            price_vs_ma5=0, price_vs_ma20=0, price_vs_ma60=0,
            is_pullback=False, pullback_depth=0, pullback_to_ma="",
            support_level=0, resistance_level=0,
            buy_signals=[], risk_signals=[]
        )
    
    def _empty_trading_points(self) -> TradingPoints:
        """返回空的交易点位"""
        return TradingPoints(
            entry_price=0, stop_loss=0,
            take_profit_1=0, take_profit_2=0, take_profit_3=0,
            entry_reason="", stop_loss_reason="",
            position_size="light", holding_period="short",
            risk_reward_ratio=0, success_probability=0
        )


if __name__ == "__main__":
    # 测试
    import numpy as np
    
    # 生成测试数据 - 模拟多头排列回调
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
    
    # 创建上升趋势后回调的数据
    base_prices = 100 * np.exp(np.linspace(0, 0.15, 100))  # 上升趋势
    noise = np.random.randn(100) * 1.5
    prices = base_prices + noise
    
    # 最后几天模拟回调
    prices[-5:] = prices[-5] * np.array([1.0, 0.99, 0.98, 0.975, 0.97])
    
    df = pd.DataFrame({
        'date': dates,
        'nav': prices
    })
    
    analyzer = EnhancedTechnicalAnalyzer()
    trend = analyzer.analyze_trend(df)
    points = analyzer.calculate_trading_points(df, trend, valuation_percentile=25)
    
    print("=" * 60)
    print("趋势分析结果")
    print("=" * 60)
    print(f"趋势方向: {trend.trend_direction}")
    print(f"趋势强度: {trend.trend_strength}")
    print(f"多头排列: {trend.is_bullish_alignment}")
    print(f"是否回调: {trend.is_pullback} (深度: {trend.pullback_depth}%)")
    print(f"回调到: {trend.pullback_to_ma}")
    print(f"\n买入信号: {trend.buy_signals}")
    print(f"风险信号: {trend.risk_signals}")
    
    print("\n" + "=" * 60)
    print("交易点位建议")
    print("=" * 60)
    print(f"买入价: {points.entry_price}")
    print(f"止损价: {points.stop_loss}")
    print(f"目标价: {points.take_profit_1} / {points.take_profit_2} / {points.take_profit_3}")
    print(f"盈亏比: {points.risk_reward_ratio}")
    print(f"成功率: {points.success_probability}%")
    print(f"建议仓位: {points.position_size}")
