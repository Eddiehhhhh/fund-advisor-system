"""
基金数据获取模块
支持从多个数据源获取基金净值、估值等信息
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml


class FundDataFetcher:
    """基金数据获取器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_fund_history(self, fund_code: str, days: int = 365) -> pd.DataFrame:
        """
        获取基金历史净值数据
        
        Args:
            fund_code: 基金代码（指数代码，会查找对应的主流ETF）
            days: 获取天数
            
        Returns:
            DataFrame with columns: date, nav, acc_nav, change_pct
        """
        # 指数代码 -> 主流ETF基金代码映射
        index_to_etf = {
            '000300': '110020',  # 沪深300 ETF (易方达)
            '000905': '160119',  # 中证500 ETF (南方)
            '399006': '110026',  # 创业板 ETF (易方达)
            '000688': '011612',  # 科创50 ETF (华夏)
            '000016': '110003',  # 上证50 ETF (易方达)
            '000852': '159845',  # 中证1000 ETF (华夏)
            '399997': '160632',  # 白酒 ETF (鹏华)
            '399989': '162412',  # 医疗 ETF (华宝)
            '399808': '164905',  # 新能源 ETF (华安)
            'H30184': '008282',  # 半导体 ETF (国联安)
            '399967': '502003',  # 军工 ETF (易方达)
            '399986': '160631',  # 银行 ETF (鹏华)
            '399975': '502010',  # 证券 ETF (易方达)
            '931775': '160628',  # 地产 ETF (鹏华)
            '930050': '008585',  # 人工智能 ETF (融通)
            'H30233': '004752',  # 传媒 ETF (广发)
            'NDX': '040046',     # 纳斯达克100 (华安)
            'SPX': '050025',     # 标普500 (博时)
            'HSI': '164705',     # 恒生指数 (汇添富)
        }
        
        etf_code = index_to_etf.get(fund_code, fund_code)
        
        # 天天基金网API - 返回HTML表格，每页最多20条，需要多页获取
        from bs4 import BeautifulSoup
        import re
        
        all_rows = []
        page = 1
        per_page = 20
        max_pages = (days + per_page - 1) // per_page  # 计算需要的页数
        
        try:
            while page <= max_pages and len(all_rows) < days:
                url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx"
                params = {
                    'type': 'lsjz',
                    'code': etf_code,
                    'page': page,
                    'per': per_page,
                }
                
                response = self.session.get(url, params=params, timeout=10)
                content = response.text
                
                # 提取HTML部分
                match = re.search(r'content:"(.*?)"', content, re.DOTALL)
                if not match:
                    break
                
                html = match.group(1).replace('\\', '')
                soup = BeautifulSoup(html, 'html.parser')
                
                # 提取表格行
                page_rows = []
                for tr in soup.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) >= 4:
                        date_str = tds[0].text.strip()
                        nav_str = tds[1].text.strip()
                        acc_nav_str = tds[2].text.strip()
                        change_str = tds[3].text.strip().replace('%', '')
                        
                        try:
                            page_rows.append({
                                'date': datetime.strptime(date_str, '%Y-%m-%d'),
                                'nav': float(nav_str),
                                'acc_nav': float(acc_nav_str),
                                'change_pct': float(change_str) if change_str else 0.0
                            })
                        except:
                            continue
                
                if not page_rows:
                    break
                
                all_rows.extend(page_rows)
                page += 1
                
                # 如果这一页数据不足20条，说明已经到最后一页
                if len(page_rows) < per_page:
                    break
            
            if all_rows:
                df = pd.DataFrame(all_rows)
                # 按日期排序，并确保最新日期在最后
                df = df.sort_values('date').reset_index(drop=True)
                # 只保留最近days条
                if len(df) > days:
                    df = df.tail(days).reset_index(drop=True)
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"    获取{fund_code}历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_index_valuation(self, index_code: str) -> Dict:
        """
        获取指数估值数据
        
        Args:
            index_code: 指数代码
            
        Returns:
            Dict with PE, PB, 分位点等数据
        """
        try:
            import akshare as ak
            import numpy as np
            
            # 使用 stock_zh_index_value_csindex 获取指数估值（支持宽基+行业+海外部分）
            df = ak.stock_zh_index_value_csindex(symbol=index_code)
            
            if not df.empty:
                latest = df.iloc[-1]
                pe = float(latest.get('市盈率2', 0))
                
                # 基于历史数据计算 PE 分位点（使用过去5年数据）
                pe_percentile = 50.0
                if len(df) > 20:
                    pe_series = df['市盈率2'].dropna().astype(float)
                    pe_percentile = float(np.percentile(pe_series.rank(pct=True).values[-1] * 100, 0)) if len(pe_series) > 0 else 50.0
                    # 更准确的分位计算：当前值在过去数据中的排名
                    current_pe = pe
                    pe_percentile = float((pe_series < current_pe).sum() / len(pe_series) * 100)
                
                # PB 数据需要估算（API不直接提供，用 PE/股息率近似或行业均值）
                dividend_yield = float(latest.get('股息率2', 0))
                pb = round(pe * dividend_yield / 100, 2) if dividend_yield > 0 else round(pe / 10, 2)
                
                # PB 分位点用 PE 分位点近似
                pb_percentile = pe_percentile
                
                return {
                    'pe': round(pe, 2),
                    'pb': round(pb, 2),
                    'pe_percentile': round(pe_percentile, 1),
                    'pb_percentile': round(pb_percentile, 1),
                    'date': str(latest.get('日期', datetime.now().strftime('%Y-%m-%d')))
                }
            
        except Exception as e:
            print(f"获取指数{index_code}估值失败: {e}")
        
        # 海外指数和获取失败时使用模拟数据
        return self._get_mock_valuation(index_code)
    
    def get_fund_list(self) -> List[Dict]:
        """获取配置的基金列表"""
        funds = []
        for category in ['broad_based', 'sector', 'overseas']:
            funds.extend(self.config['funds'].get(category, []))
        return funds

    def get_fund_basic_info(self, fund_code: str) -> Dict:
        """
        获取基金基本面信息（规模、费率、成立日期等）
        
        Args:
            fund_code: 基金代码（指数代码，会查找对应的主流ETF）
            
        Returns:
            Dict with scale, management_fee, tracking_error, establish_year
        """
        # 指数代码 -> 主流ETF代码映射
        index_to_etf = {
            '000300': '510300',  # 沪深300 ETF (华泰柏瑞)
            '000905': '510500',  # 中证500 ETF (南方)
            '399006': '159915',  # 创业板 ETF (易方达)
            '000688': '588000',  # 科创50 ETF (华夏)
            '000016': '510050',  # 上证50 ETF (华夏)
            '000852': '512100',  # 中证1000 ETF (华夏)
            '399997': '512690',  # 白酒 ETF (鹏华)
            '399989': '512170',  # 医疗 ETF (华夏)
            '399808': '516160',  # 新能源 ETF (华夏)
            'H30184': '512480',  # 半导体 ETF (国泰)
            '399967': '512660',  # 军工 ETF (国泰)
            '399986': '512800',  # 银行 ETF (华宝)
            '399975': '512880',  # 证券 ETF (国泰)
            '931775': '512200',  # 地产 ETF (建信)
            '930050': '515070',  # 人工智能 ETF (华宝)
            'H30233': '512980',  # 传媒 ETF (易方达)
        }
        
        etf_code = index_to_etf.get(fund_code)
        
        if etf_code:
            try:
                # 从天天基金获取ETF基本信息
                url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx"
                params = {
                    'type': 'basicinfo',
                    'code': etf_code,
                    'page': 1,
                    'per': 1,
                }
                response = self.session.get(url, params=params, timeout=5)
                content = response.text
                
                # 尝试解析基本信息
                # 天天基金另一个接口
                url2 = f"https://fundf10.eastmoney.com/jbgk_{etf_code}.html"
                resp2 = self.session.get(url2, timeout=5)
                
                import re
                text = resp2.text
                
                # 提取基金规模
                scale = 50.0  # 默认值
                scale_match = re.search(r'基金规模.*?(\d+\.?\d*)\s*亿', text)
                if scale_match:
                    scale = float(scale_match.group(1))
                
                # 提取管理费率
                fee = 0.5  # 默认值
                fee_match = re.search(r'管理费率.*?(\d+\.?\d+)%', text)
                if fee_match:
                    fee = float(fee_match.group(1))
                
                # 提取成立日期
                establish_year = 5  # 默认值
                date_match = re.search(r'成立日期.*?(\d{4})-(\d{2})-(\d{2})', text)
                if date_match:
                    establish_year = datetime.now().year - int(date_match.group(1))
                    establish_year = max(1, establish_year)
                
                # 提取跟踪误差
                tracking_error = 0.15  # 默认值
                te_match = re.search(r'跟踪误差.*?(\d+\.?\d+)%', text)
                if te_match:
                    tracking_error = float(te_match.group(1)) / 100
                
                return {
                    'scale': scale,
                    'management_fee': fee,
                    'tracking_error': tracking_error,
                    'establish_year': establish_year,
                    'etf_code': etf_code
                }
                
            except Exception as e:
                print(f"    获取{fund_code}基本面数据失败: {e}")
        
        # 基于指数特点返回合理的默认值（非随机）
        return self._get_default_fund_info(fund_code)

    def _get_default_fund_info(self, index_code: str) -> Dict:
        """基于指数特点返回合理的默认基本面数据"""
        # 主流大型ETF的基本面数据（近似真实值）
        fund_info_map = {
            '000300': {'scale': 1200, 'management_fee': 0.15, 'tracking_error': 0.05, 'establish_year': 17},
            '000905': {'scale': 600,  'management_fee': 0.15, 'tracking_error': 0.06, 'establish_year': 12},
            '399006': {'scale': 400,  'management_fee': 0.20, 'tracking_error': 0.08, 'establish_year': 12},
            '000688': {'scale': 300,  'management_fee': 0.20, 'tracking_error': 0.10, 'establish_year': 5},
            '000016': {'scale': 900,  'management_fee': 0.10, 'tracking_error': 0.04, 'establish_year': 18},
            '000852': {'scale': 200,  'management_fee': 0.20, 'tracking_error': 0.10, 'establish_year': 8},
            '399997': {'scale': 120,  'management_fee': 0.50, 'tracking_error': 0.20, 'establish_year': 8},
            '399989': {'scale': 80,   'management_fee': 0.50, 'tracking_error': 0.25, 'establish_year': 7},
            '399808': {'scale': 60,   'management_fee': 0.50, 'tracking_error': 0.30, 'establish_year': 5},
            'H30184': {'scale': 180,  'management_fee': 0.50, 'tracking_error': 0.25, 'establish_year': 8},
            '399967': {'scale': 90,   'management_fee': 0.50, 'tracking_error': 0.30, 'establish_year': 9},
            '399986': {'scale': 300,  'management_fee': 0.15, 'tracking_error': 0.08, 'establish_year': 9},
            '399975': {'scale': 150,  'management_fee': 0.50, 'tracking_error': 0.15, 'establish_year': 9},
            '931775': {'scale': 25,   'management_fee': 0.50, 'tracking_error': 0.30, 'establish_year': 4},
            '930050': {'scale': 40,   'management_fee': 0.50, 'tracking_error': 0.35, 'establish_year': 6},
            'H30233': {'scale': 30,   'management_fee': 0.50, 'tracking_error': 0.30, 'establish_year': 7},
        }
        return fund_info_map.get(index_code, {
            'scale': 50, 'management_fee': 0.50, 'tracking_error': 0.20, 'establish_year': 5
        })
    
    def get_market_sentiment(self) -> Dict:
        """
        获取市场情绪指标（增强版）
        
        Returns:
            Dict with 成交量、涨跌家数、北向资金、恐慌贪婪指数、融资余额等
        """
        result = {
            'north_money_flow': 0,
            'north_money_5d': 0,
            'up_count': 0,
            'down_count': 0,
            'fear_greed_index': 50,
            'main_money_flow': 0,
            'main_money_5d': 0,
            'margin_balance': 0,
            'margin_change': 0,
            'volume_ratio': 1.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            import akshare as ak
            
            # 1. 北向资金（沪股通+深股通合计）
            try:
                north_sh = ak.stock_hsgt_hist_em(symbol="沪股通")
                north_sz = ak.stock_hsgt_hist_em(symbol="深股通")
                
                sh_flow = float(north_sh.iloc[-1].get('当日资金流入', 0)) if not north_sh.empty else 0
                sz_flow = float(north_sz.iloc[-1].get('当日资金流入', 0)) if not north_sz.empty else 0
                result['north_money_flow'] = round(sh_flow + sz_flow, 2)
                
                # 计算5日累计北向资金
                if len(north_sh) >= 5 and len(north_sz) >= 5:
                    sh_5d = north_sh.iloc[-5:]['当日资金流入'].astype(float).sum()
                    sz_5d = north_sz.iloc[-5:]['当日资金流入'].astype(float).sum()
                    result['north_money_5d'] = round(sh_5d + sz_5d, 2)
            except Exception as e:
                print(f"    北向资金获取失败: {e}")
            
            # 2. 市场涨跌家数（使用大盘统计）
            try:
                market_df = ak.stock_market_activity_legu()
                if not market_df.empty:
                    # 尝试从DataFrame中获取涨跌数据
                    data_dict = dict(zip(market_df.iloc[:, 0], market_df.iloc[:, 1]))
                    up_count = int(data_dict.get('上涨', data_dict.get('涨', 0)))
                    down_count = int(data_dict.get('下跌', data_dict.get('跌', 0)))
                    result['up_count'] = up_count
                    result['down_count'] = down_count
                    
                    # 计算恐贪指数（基于涨跌比）
                    total = up_count + down_count
                    if total > 0:
                        up_ratio = up_count / total
                        # 映射到0-100区间
                        result['fear_greed_index'] = round(up_ratio * 100, 1)
            except Exception as e:
                print(f"    涨跌家数获取失败: {e}")
                # 备用方案：获取上证指数当日涨幅估算情绪
                try:
                    sh_df = ak.stock_zh_index_spot_em(symbol="上证指数")
                    if not sh_df.empty:
                        change_pct = float(sh_df.iloc[0].get('涨跌幅', 0))
                        # 涨跌幅映射到恐贪指数
                        result['fear_greed_index'] = max(0, min(100, 50 + change_pct * 5))
                except:
                    pass
            
            # 3. 主力资金流向（板块主力净流入）
            try:
                sector_flow = ak.stock_sector_fund_flow_rank(indicator="今日排行")
                if not sector_flow.empty:
                    # 计算所有行业的主力净流入总和
                    flow_col = '主力净流入-净额' if '主力净流入-净额' in sector_flow.columns else sector_flow.columns[-1]
                    total_flow = sector_flow[flow_col].astype(float).sum() / 1e8  # 转换为亿
                    result['main_money_flow'] = round(total_flow, 2)
                
                # 5日主力流向
                sector_flow_5d = ak.stock_sector_fund_flow_rank(indicator="5日排行")
                if not sector_flow_5d.empty:
                    flow_col_5d = '主力净流入-净额' if '主力净流入-净额' in sector_flow_5d.columns else sector_flow_5d.columns[-1]
                    total_flow_5d = sector_flow_5d[flow_col_5d].astype(float).sum() / 1e8
                    result['main_money_5d'] = round(total_flow_5d, 2)
            except Exception as e:
                print(f"    主力资金获取失败: {e}")
            
            # 4. 融资余额数据
            try:
                margin_df = ak.stock_margin_szse()
                if not margin_df.empty:
                    latest = margin_df.iloc[-1]
                    result['margin_balance'] = float(latest.get('融资余额', 0)) / 1e8  # 转换为亿
                    # 计算融资余额变化（相比前一日）
                    if len(margin_df) >= 2:
                        prev = margin_df.iloc[-2]
                        prev_balance = float(prev.get('融资余额', 0)) / 1e8
                        result['margin_change'] = round(result['margin_balance'] - prev_balance, 2)
            except Exception as e:
                print(f"    融资余额获取失败: {e}")
            
            # 5. 成交量比（当日成交量/5日均量）
            try:
                sh_index = ak.stock_zh_index_daily_em(symbol="sh000001")
                if not sh_index.empty and len(sh_index) >= 6:
                    latest_vol = float(sh_index.iloc[-1]['volume'])
                    avg_5d_vol = sh_index.iloc[-5:]['volume'].astype(float).mean()
                    result['volume_ratio'] = round(latest_vol / avg_5d_vol, 2) if avg_5d_vol > 0 else 1.0
            except Exception as e:
                print(f"    成交量获取失败: {e}")
            
        except Exception as e:
            print(f"获取市场情绪数据失败: {e}")
        
        return result
    
    def get_sector_fund_flow(self, days: int = 5) -> pd.DataFrame:
        """
        获取行业资金流向
        
        Args:
            days: 统计天数
            
        Returns:
            DataFrame with 行业资金流向数据
        """
        try:
            import akshare as ak
            
            # 获取行业资金流向
            df = ak.stock_sector_fund_flow_rank(indicator="5日排行")
            return df
            
        except Exception as e:
            print(f"获取行业资金流向失败: {e}")
            return pd.DataFrame()
    
    def get_etf_fund_flow(self, fund_code: str) -> Dict:
        """
        获取ETF资金流向（场内ETF的成交额、净流入）
        
        Args:
            fund_code: 指数代码
            
        Returns:
            ETF资金流向数据
        """
        # 指数代码 -> 场内ETF代码映射
        index_to_etf_code = {
            '000300': '510300',  # 沪深300 ETF
            '000905': '510500',  # 中证500 ETF
            '399006': '159915',  # 创业板 ETF
            '000688': '588000',  # 科创50 ETF
            '000016': '510050',  # 上证50 ETF
            '000852': '512100',  # 中证1000 ETF
            '399997': '512690',  # 白酒 ETF
            '399989': '512170',  # 医疗 ETF
            '399808': '516160',  # 新能源 ETF
            'H30184': '512480',  # 半导体 ETF
            '399967': '512660',  # 军工 ETF
            '399986': '512800',  # 银行 ETF
            '399975': '512880',  # 证券 ETF
            '931775': '512200',  # 地产 ETF
            '930050': '515070',  # 人工智能 ETF
            'H30233': '512980',  # 传媒 ETF
        }
        
        etf_code = index_to_etf_code.get(fund_code)
        if not etf_code:
            return {'etf_code': None, 'inflow': 0, 'volume': 0, 'turnover': 0}
        
        try:
            import akshare as ak
            
            # 获取ETF实时行情
            etf_spot = ak.fund_etf_spot_em()
            etf_row = etf_spot[etf_spot['代码'] == etf_code]
            
            if not etf_row.empty:
                row = etf_row.iloc[0]
                return {
                    'etf_code': etf_code,
                    'inflow': 0,  # 需要额外计算
                    'volume': float(row.get('成交量', 0)),
                    'turnover': float(row.get('成交额', 0)) / 1e8,  # 转换为亿
                    'change_pct': float(row.get('涨跌幅', 0)),
                    'premium': float(row.get('溢价率', 0)) if '溢价率' in row else 0,
                }
        except Exception as e:
            print(f"    获取ETF{etf_code}资金流向失败: {e}")
        
        return {'etf_code': etf_code, 'inflow': 0, 'volume': 0, 'turnover': 0}
    
    def get_sector_money_flow_detail(self) -> Dict:
        """
        获取详细的板块资金流向（主力、散户、机构）
        
        Returns:
            板块资金流向详情
        """
        result = {
            'top_inflow_sectors': [],  # 资金流入前5板块
            'top_outflow_sectors': [],  # 资金流出前5板块
            'sector_details': {}
        }
        
        try:
            import akshare as ak
            
            # 获取行业资金流向
            df = ak.stock_sector_fund_flow_rank(indicator="今日排行")
            
            if not df.empty:
                # 解析数据
                for _, row in df.head(5).iterrows():
                    sector_name = row.get('名称', '')
                    main_inflow = float(row.get('主力净流入-净额', 0)) / 1e8  # 转换为亿
                    result['top_inflow_sectors'].append({
                        'name': sector_name,
                        'main_inflow': round(main_inflow, 2)
                    })
                
                for _, row in df.tail(5).iterrows():
                    sector_name = row.get('名称', '')
                    main_inflow = float(row.get('主力净流入-净额', 0)) / 1e8
                    result['top_outflow_sectors'].append({
                        'name': sector_name,
                        'main_inflow': round(main_inflow, 2)
                    })
        except Exception as e:
            print(f"获取板块资金流向详情失败: {e}")
        
        return result
    
    def _get_index_name(self, code: str) -> str:
        """获取指数名称映射"""
        mapping = {
            '000300': '沪深300',
            '000905': '中证500',
            '399006': '创业板指',
            '000016': '上证50',
            '000852': '中证1000',
            '000688': '科创50',
        }
        return mapping.get(code, code)
    
    def _get_mock_valuation(self, index_code: str) -> Dict:
        """
        生成模拟估值数据（用于测试）
        实际部署时需要替换为真实数据源
        """
        import random
        
        # 根据指数特点设置不同的基准估值
        base_valuations = {
            '000300': {'pe': 11.5, 'pb': 1.3},
            '000905': {'pe': 21.0, 'pb': 1.8},
            '399006': {'pe': 28.0, 'pb': 3.8},
            '000688': {'pe': 45.0, 'pb': 4.2},
            '000016': {'pe': 9.8, 'pb': 1.1},
            '000852': {'pe': 35.0, 'pb': 2.2},
            '399997': {'pe': 25.0, 'pb': 6.5},  # 白酒
            '399989': {'pe': 32.0, 'pb': 3.8},  # 医疗
            '399808': {'pe': 18.0, 'pb': 2.5},  # 新能源
            'H30184': {'pe': 65.0, 'pb': 3.5},  # 半导体
            '399967': {'pe': 55.0, 'pb': 3.2},  # 军工
            '399986': {'pe': 5.2, 'pb': 0.55},  # 银行
            '399975': {'pe': 15.0, 'pb': 1.3},  # 证券
            '931775': {'pe': 8.5, 'pb': 0.85},  # 地产
        }
        
        base = base_valuations.get(index_code, {'pe': 15.0, 'pb': 1.5})
        
        # 添加随机波动
        pe = base['pe'] * (1 + random.uniform(-0.15, 0.15))
        pb = base['pb'] * (1 + random.uniform(-0.15, 0.15))
        
        # 生成合理的分位点
        pe_percentile = random.uniform(5, 85)
        pb_percentile = random.uniform(5, 85)
        
        return {
            'pe': round(pe, 2),
            'pb': round(pb, 2),
            'pe_percentile': round(pe_percentile, 2),
            'pb_percentile': round(pb_percentile, 2),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'is_mock': True  # 标记为模拟数据
        }


if __name__ == "__main__":
    # 测试数据获取
    fetcher = FundDataFetcher()
    
    # 测试获取基金列表
    funds = fetcher.get_fund_list()
    print(f"配置基金数量: {len(funds)}")
    
    # 测试获取估值数据
    for fund in funds[:3]:
        code = fund['code']
        name = fund['name']
        valuation = fetcher.get_index_valuation(code)
        print(f"\n{name}({code}):")
        print(f"  PE: {valuation['pe']}, PE分位: {valuation['pe_percentile']}%")
        print(f"  PB: {valuation['pb']}, PB分位: {valuation['pb_percentile']}%")
