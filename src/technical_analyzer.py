"""
技术分析模块
计算各种技术指标：移动平均线、RSI、MACD、布林带等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TechnicalIndicators:
    """技术指标数据类（增强版）"""
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    ma_20: float
    ma_60: float
    boll_upper: float
    boll_middle: float
    boll_lower: float
    price_position: float  # 价格在布林带中的位置 (0-1)
    trend_direction: str   # up/down/sideways
    volatility: float      # 波动率
    # 新增指标
    kdj_k: float          # KDJ-K值
    kdj_d: float          # KDJ-D值
    kdj_j: float          # KDJ-J值
    williams_r: float     # 威廉指标
    cci: float            # CCI指标
    atr: float            # 真实波动幅度
    support_level: float  # 支撑位
    resistance_level: float  # 阻力位
    volume_trend: str     # 成交量趋势
    pattern_signals: List[str]  # 形态信号列表


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self, rsi_period: int = 14, 
                 ma_short: int = 20, ma_long: int = 60,
                 boll_period: int = 20, boll_std: float = 2.0):
        self.rsi_period = rsi_period
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.boll_period = boll_period
        self.boll_std = boll_std
    
    def calculate_rsi(self, prices: pd.Series) -> float:
        """
        计算RSI指标
        
        Args:
            prices: 价格序列
            
        Returns:
            RSI值 (0-100)
        """
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        # 计算价格变化
        delta = prices.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """
        计算MACD指标
        
        Args:
            prices: 价格序列
            
        Returns:
            (macd, signal, histogram)
        """
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        # 计算EMA
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        
        # MACD线
        macd = ema_12 - ema_26
        
        # 信号线
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # MACD柱状图
        histogram = macd - signal
        
        return (
            macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0.0,
            signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0.0,
            histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0.0
        )
    
    def calculate_bollinger(self, prices: pd.Series) -> Tuple[float, float, float]:
        """
        计算布林带
        
        Args:
            prices: 价格序列
            
        Returns:
            (upper, middle, lower)
        """
        if len(prices) < self.boll_period:
            current_price = prices.iloc[-1]
            return current_price * 1.02, current_price, current_price * 0.98
        
        # 中轨 = N日移动平均线
        middle = prices.rolling(window=self.boll_period).mean()
        
        # 标准差
        std = prices.rolling(window=self.boll_period).std()
        
        # 上轨和下轨
        upper = middle + (std * self.boll_std)
        lower = middle - (std * self.boll_std)
        
        return (
            upper.iloc[-1] if not pd.isna(upper.iloc[-1]) else prices.iloc[-1],
            middle.iloc[-1] if not pd.isna(middle.iloc[-1]) else prices.iloc[-1],
            lower.iloc[-1] if not pd.isna(lower.iloc[-1]) else prices.iloc[-1]
        )
    
    def calculate_moving_averages(self, prices: pd.Series) -> Tuple[float, float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格序列
            
        Returns:
            (ma_short, ma_long)
        """
        ma_s = prices.rolling(window=self.ma_short).mean().iloc[-1]
        ma_l = prices.rolling(window=self.ma_long).mean().iloc[-1]
        
        return (
            ma_s if not pd.isna(ma_s) else prices.iloc[-1],
            ma_l if not pd.isna(ma_l) else prices.iloc[-1]
        )
    
    def calculate_volatility(self, prices: pd.Series) -> float:
        """
        计算波动率 (20日收益率标准差)
        
        Args:
            prices: 价格序列
            
        Returns:
            年化波动率
        """
        if len(prices) < 20:
            return 0.2  # 默认20%
        
        # 计算日收益率
        returns = prices.pct_change().dropna()
        
        # 20日标准差，年化
        volatility = returns.tail(20).std() * np.sqrt(252)
        
        return volatility if not pd.isna(volatility) else 0.2
    
    def calculate_kdj(self, prices: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[float, float, float]:
        """
        计算KDJ指标
        
        Args:
            prices: 价格序列
            n: RSV计算周期
            m1: K平滑系数
            m2: D平滑系数
            
        Returns:
            (K值, D值, J值)
        """
        if len(prices) < n:
            return 50.0, 50.0, 50.0
        
        # 计算RSV
        low_list = prices.rolling(window=n, min_periods=n).min()
        high_list = prices.rolling(window=n, min_periods=n).max()
        rsv = (prices - low_list) / (high_list - low_list) * 100
        
        # 计算K、D、J
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return (
            k.iloc[-1] if not pd.isna(k.iloc[-1]) else 50.0,
            d.iloc[-1] if not pd.isna(d.iloc[-1]) else 50.0,
            j.iloc[-1] if not pd.isna(j.iloc[-1]) else 50.0
        )
    
    def calculate_williams_r(self, prices: pd.Series, n: int = 14) -> float:
        """
        计算威廉指标(Williams %R)
        
        Args:
            prices: 价格序列
            n: 计算周期
            
        Returns:
            Williams %R值 (-100到0)
        """
        if len(prices) < n:
            return -50.0
        
        high = prices.rolling(window=n).max()
        low = prices.rolling(window=n).min()
        wr = (high - prices) / (high - low) * (-100)
        
        return wr.iloc[-1] if not pd.isna(wr.iloc[-1]) else -50.0
    
    def calculate_cci(self, prices: pd.Series, n: int = 20) -> float:
        """
        计算CCI指标(商品通道指数)
        
        Args:
            prices: 价格序列
            n: 计算周期
            
        Returns:
            CCI值
        """
        if len(prices) < n:
            return 0.0
        
        tp = prices  # 典型价格简化为收盘价
        ma = tp.rolling(window=n).mean()
        md = tp.rolling(window=n).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - ma) / (0.015 * md)
        
        return cci.iloc[-1] if not pd.isna(cci.iloc[-1]) else 0.0
    
    def calculate_atr(self, prices: pd.Series, n: int = 14) -> float:
        """
        计算ATR(真实波动幅度)
        
        Args:
            prices: 价格序列
            n: 计算周期
            
        Returns:
            ATR值
        """
        if len(prices) < n + 1:
            return prices.std() if len(prices) > 1 else 0.0
        
        high = prices
        low = prices
        close_prev = prices.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=n).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0
    
    def find_support_resistance(self, prices: pd.Series, window: int = 20) -> Tuple[float, float]:
        """
        寻找支撑位和阻力位
        
        Args:
            prices: 价格序列
            window: 观察窗口
            
        Returns:
            (支撑位, 阻力位)
        """
        if len(prices) < window:
            current = prices.iloc[-1]
            return current * 0.95, current * 1.05
        
        recent_prices = prices.tail(window)
        
        # 简单方法：近期最低价为支撑，近期最高价为阻力
        support = recent_prices.min()
        resistance = recent_prices.max()
        
        return support, resistance
    
    def detect_patterns(self, df: pd.DataFrame) -> List[str]:
        """
        检测K线形态信号
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            形态信号列表
        """
        patterns = []
        
        if len(df) < 5:
            return patterns
        
        prices = df['nav'].values
        
        # 获取最近5天的价格
        recent = prices[-5:]
        
        # 检测双底形态 (简化版)
        if len(recent) >= 4:
            if recent[-4] > recent[-3] < recent[-2] > recent[-1]:
                # 价格形成W形状
                if abs(recent[-3] - recent[-1]) / recent[-3] < 0.02:  # 底部接近
                    patterns.append("潜在双底形态")
        
        # 检测头肩底 (简化版)
        if len(recent) >= 5:
            if recent[-5] > recent[-4] < recent[-3] > recent[-2] < recent[-1]:
                if recent[-4] < recent[-2]:  # 左肩低于右肩
                    patterns.append("潜在头肩底形态")
        
        # 检测连续下跌后的反弹
        if len(df) >= 10:
            last_5 = prices[-5:]
            prev_5 = prices[-10:-5]
            if np.mean(last_5) < np.mean(prev_5) * 0.95:  # 近期下跌5%以上
                if prices[-1] > prices[-2]:  # 今天反弹
                    patterns.append("超跌反弹信号")
        
        # 检测突破
        if len(df) >= 20:
            ma20 = df['nav'].rolling(window=20).mean().iloc[-1]
            current = prices[-1]
            prev = prices[-2]
            
            if prev < ma20 and current > ma20:  # 向上突破20日均线
                patterns.append("突破20日均线")
            elif prev > ma20 and current < ma20:  # 向下跌破20日均线
                patterns.append("跌破20日均线")
        
        return patterns
    
    def analyze(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        综合分析，计算所有技术指标（增强版）
        
        Args:
            df: 包含date和nav列的DataFrame
            
        Returns:
            TechnicalIndicators对象
        """
        if df.empty or len(df) < 30:
            # 数据不足，返回默认值
            return TechnicalIndicators(
                rsi=50.0, macd=0.0, macd_signal=0.0, macd_hist=0.0,
                ma_20=0.0, ma_60=0.0, boll_upper=0.0, boll_middle=0.0, boll_lower=0.0,
                price_position=0.5, trend_direction='sideways', volatility=0.2,
                kdj_k=50.0, kdj_d=50.0, kdj_j=50.0, williams_r=-50.0, cci=0.0, atr=0.0,
                support_level=0.0, resistance_level=0.0, volume_trend='neutral',
                pattern_signals=[]
            )
        
        prices = df['nav']
        current_price = prices.iloc[-1]
        
        # 计算各项指标
        rsi = self.calculate_rsi(prices)
        macd, macd_signal, macd_hist = self.calculate_macd(prices)
        ma_20, ma_60 = self.calculate_moving_averages(prices)
        boll_upper, boll_middle, boll_lower = self.calculate_bollinger(prices)
        volatility = self.calculate_volatility(prices)
        
        # 计算新增指标
        kdj_k, kdj_d, kdj_j = self.calculate_kdj(prices)
        williams_r = self.calculate_williams_r(prices)
        cci = self.calculate_cci(prices)
        atr = self.calculate_atr(prices)
        support_level, resistance_level = self.find_support_resistance(prices)
        pattern_signals = self.detect_patterns(df)
        
        # 计算价格在布林带中的位置
        if boll_upper != boll_lower:
            price_position = (current_price - boll_lower) / (boll_upper - boll_lower)
            price_position = max(0, min(1, price_position))
        else:
            price_position = 0.5
        
        # 判断趋势方向
        if ma_20 > ma_60 * 1.02:
            trend_direction = 'up'
        elif ma_20 < ma_60 * 0.98:
            trend_direction = 'down'
        else:
            trend_direction = 'sideways'
        
        # 成交量趋势（简化判断）
        if len(df) >= 10:
            recent_vol = df['change_pct'].tail(5).abs().mean()
            prev_vol = df['change_pct'].tail(10).head(5).abs().mean()
            if recent_vol > prev_vol * 1.2:
                volume_trend = 'increasing'
            elif recent_vol < prev_vol * 0.8:
                volume_trend = 'decreasing'
            else:
                volume_trend = 'neutral'
        else:
            volume_trend = 'neutral'
        
        return TechnicalIndicators(
            rsi=round(rsi, 2),
            macd=round(macd, 4),
            macd_signal=round(macd_signal, 4),
            macd_hist=round(macd_hist, 4),
            ma_20=round(ma_20, 4),
            ma_60=round(ma_60, 4),
            boll_upper=round(boll_upper, 4),
            boll_middle=round(boll_middle, 4),
            boll_lower=round(boll_lower, 4),
            price_position=round(price_position, 4),
            trend_direction=trend_direction,
            volatility=round(volatility, 4),
            kdj_k=round(kdj_k, 2),
            kdj_d=round(kdj_d, 2),
            kdj_j=round(kdj_j, 2),
            williams_r=round(williams_r, 2),
            cci=round(cci, 2),
            atr=round(atr, 4),
            support_level=round(support_level, 4),
            resistance_level=round(resistance_level, 4),
            volume_trend=volume_trend,
            pattern_signals=pattern_signals
        )
    
    def get_buy_signals(self, indicators: TechnicalIndicators) -> List[str]:
        """
        获取买入信号列表
        
        Args:
            indicators: 技术指标对象
            
        Returns:
            买入信号列表
        """
        signals = []
        
        # RSI超卖
        if indicators.rsi < 30:
            signals.append("RSI超卖")
        elif indicators.rsi < 40:
            signals.append("RSI接近超卖")
        
        # MACD金叉
        if indicators.macd_hist > 0 and indicators.macd > indicators.macd_signal:
            signals.append("MACD金叉")
        
        # 价格触及布林带下轨
        if indicators.price_position < 0.1:
            signals.append("价格触及布林带下轨")
        elif indicators.price_position < 0.2:
            signals.append("价格接近布林带下轨")
        
        # 均线金叉
        if indicators.ma_20 > indicators.ma_60:
            signals.append("短期均线上穿长期均线")
        
        return signals
    
    def get_sell_signals(self, indicators: TechnicalIndicators) -> List[str]:
        """
        获取卖出信号列表
        
        Args:
            indicators: 技术指标对象
            
        Returns:
            卖出信号列表
        """
        signals = []
        
        # RSI超买
        if indicators.rsi > 70:
            signals.append("RSI超买")
        
        # MACD死叉
        if indicators.macd_hist < 0 and indicators.macd < indicators.macd_signal:
            signals.append("MACD死叉")
        
        # 价格触及布林带上轨
        if indicators.price_position > 0.9:
            signals.append("价格触及布林带上轨")
        
        return signals


if __name__ == "__main__":
    # 测试技术分析
    import numpy as np
    
    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
    prices = 100 * np.cumprod(1 + np.random.randn(100) * 0.02)
    
    df = pd.DataFrame({
        'date': dates,
        'nav': prices
    })
    
    analyzer = TechnicalAnalyzer()
    indicators = analyzer.analyze(df)
    
    print("技术指标分析结果:")
    print(f"RSI: {indicators.rsi}")
    print(f"MACD: {indicators.macd}, Signal: {indicators.macd_signal}, Hist: {indicators.macd_hist}")
    print(f"MA20: {indicators.ma_20}, MA60: {indicators.ma_60}")
    print(f"布林带: 上轨{indicators.boll_upper}, 中轨{indicators.boll_middle}, 下轨{indicators.boll_lower}")
    print(f"价格位置: {indicators.price_position}")
    print(f"趋势: {indicators.trend_direction}")
    print(f"波动率: {indicators.volatility}")
    
    buy_signals = analyzer.get_buy_signals(indicators)
    sell_signals = analyzer.get_sell_signals(indicators)
    
    print(f"\n买入信号: {buy_signals}")
    print(f"卖出信号: {sell_signals}")
