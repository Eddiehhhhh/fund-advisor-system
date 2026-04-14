"""
新闻舆情分析模块
实时抓取基金相关新闻，分析情绪，提取关键信息
"""

import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
import time


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    content: str
    source: str
    url: str
    publish_time: str
    sentiment: str  # positive/negative/neutral
    relevance: float  # 相关度 0-1
    keywords: List[str]


@dataclass
class SentimentAnalysis:
    """情绪分析结果"""
    overall_sentiment: str  # bullish/bearish/neutral
    sentiment_score: float  # -1 到 1
    positive_count: int
    negative_count: int
    neutral_count: int
    
    # 热点关键词
    hot_keywords: List[Tuple[str, int]]  # (关键词, 出现次数)
    
    # 重要新闻
    key_news: List[NewsItem]
    
    # 情绪趋势
    sentiment_trend: str  # improving/worsening/stable


class FundNewsAnalyzer:
    """基金新闻分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 基金名称映射
        self.fund_keywords = {
            "沪深300": ["沪深300", "大盘", "蓝筹股", "核心资产"],
            "中证500": ["中证500", "中小盘", "成长股"],
            "创业板指": ["创业板", "创指", "成长股", "新能源", "医药"],
            "科创50": ["科创50", "科创板", "硬科技", "半导体", "芯片"],
            "中证白酒": ["白酒", "茅台", "五粮液", "泸州老窖", "消费"],
            "中证医疗": ["医疗", "医药", "生物医药", "创新药", "CXO", "集采"],
            "中证新能源": ["新能源", "光伏", "锂电", "储能", "宁德时代", "比亚迪"],
            "中证半导体": ["半导体", "芯片", "集成电路", "中芯国际", "设备材料"],
            "中证军工": ["军工", "国防", "航空航天", "船舶"],
            "中证银行": ["银行", "银行股", "息差", "高股息"],
            "证券公司": ["券商", "证券", "投行", "成交量", "牛市"],
            "中证房地产": ["房地产", "地产", "房价", "销售", "保交楼"],
            "中证人工智能": ["人工智能", "AI", "ChatGPT", "大模型", "算力", "AIGC"],
            "中证传媒": ["传媒", "游戏", "短剧", "影视", "出版"],
            "纳斯达克100": ["纳斯达克", "美股", "科技股", "英伟达", "苹果", "微软"],
            "标普500": ["标普500", "美股", "美国经济", "美联储"],
            "恒生指数": ["恒生", "港股", "香港", "南向资金"],
            "恒生科技": ["恒生科技", "港股科技", "腾讯", "阿里", "美团", "小米"],
            "有色金属": ["有色", "铜", "铝", "锂", "稀土", "大宗商品"],
        }
        
        # 情绪词库
        self.positive_words = [
            "上涨", "大涨", "反弹", "突破", "利好", "看好", "推荐", "买入", "增持",
            "强劲", "爆发", "创新高", "超预期", "改善", "复苏", "景气", "繁荣",
            "机会", "机遇", "黄金坑", "底部", "低估", "价值", "潜力", "龙头",
            "领涨", "强势", "企稳", "回升", "修复", "向好", "乐观", "信心"
        ]
        
        self.negative_words = [
            "下跌", "大跌", "调整", "回调", "破位", "利空", "看空", "卖出", "减持",
            "疲软", "崩盘", "创新低", "不及预期", "恶化", "衰退", "低迷", "危机",
            "风险", "警惕", "泡沫", "顶部", "高估", "泡沫", "衰退", "暴雷",
            "领跌", "弱势", "震荡", "下跌", "向坏", "悲观", "担忧", "恐慌"
        ]
    
    def fetch_news_from_eastmoney(self, keyword: str, days: int = 3) -> List[NewsItem]:
        """
        从东方财富获取新闻
        """
        news_list = []
        
        try:
            # 东方财富搜索API
            url = "https://searchapi.eastmoney.com/api/suggest/get"
            params = {
                'input': keyword,
                'type': 14,  # 新闻类型
                'count': 20,
                'market': 'cn',
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'QuotationCodeTable' in data and 'Data' in data['QuotationCodeTable']:
                for item in data['QuotationCodeTable']['Data']:
                    news = NewsItem(
                        title=item.get('Title', ''),
                        content=item.get('Description', ''),
                        source=item.get('Source', '东方财富'),
                        url=item.get('Url', ''),
                        publish_time=item.get('ShowTime', datetime.now().strftime('%Y-%m-%d')),
                        sentiment=self._analyze_sentiment(item.get('Title', '') + item.get('Description', '')),
                        relevance=0.8,
                        keywords=self._extract_keywords(item.get('Title', ''))
                    )
                    news_list.append(news)
            
        except Exception as e:
            print(f"获取东方财富新闻失败: {e}")
        
        return news_list
    
    def fetch_news_from_sina(self, keyword: str) -> List[NewsItem]:
        """
        从新浪财经获取新闻
        """
        news_list = []
        
        try:
            url = f"https://search.sina.com.cn/?q={keyword}&c=news&from=channel&ie=utf-8"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析新闻列表
            news_items = soup.find_all('div', class_='box-result clearfix')
            
            for item in news_items[:10]:
                try:
                    title_tag = item.find('h2')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        link = title_tag.find('a')['href'] if title_tag.find('a') else ''
                        
                        content_tag = item.find('p', class_='content')
                        content = content_tag.get_text(strip=True) if content_tag else ''
                        
                        source_tag = item.find('span', class_='fgray_time')
                        source = source_tag.get_text(strip=True) if source_tag else '新浪'
                        
                        news = NewsItem(
                            title=title,
                            content=content,
                            source=source,
                            url=link,
                            publish_time=datetime.now().strftime('%Y-%m-%d'),
                            sentiment=self._analyze_sentiment(title + content),
                            relevance=0.7,
                            keywords=self._extract_keywords(title)
                        )
                        news_list.append(news)
                except:
                    continue
                    
        except Exception as e:
            print(f"获取新浪新闻失败: {e}")
        
        return news_list
    
    def fetch_fund_news(self, fund_name: str) -> List[NewsItem]:
        """
        获取特定基金相关新闻
        """
        all_news = []
        
        # 获取关键词列表
        keywords = self.fund_keywords.get(fund_name, [fund_name])
        
        # 从多个来源获取
        for keyword in keywords[:2]:  # 取前2个关键词避免过多请求
            all_news.extend(self.fetch_news_from_eastmoney(keyword))
            time.sleep(0.5)  # 避免请求过快
        
        # 去重并按时间排序
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news.title not in seen_titles:
                seen_titles.add(news.title)
                unique_news.append(news)
        
        return unique_news[:15]  # 返回最多15条
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        分析文本情绪
        """
        text = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        """
        keywords = []
        
        # 检查情绪词
        for word in self.positive_words + self.negative_words:
            if word in text:
                keywords.append(word)
        
        return list(set(keywords))[:5]  # 最多5个关键词
    
    def analyze_fund_sentiment(self, fund_name: str) -> SentimentAnalysis:
        """
        分析特定基金的市场情绪
        """
        # 获取新闻
        news_list = self.fetch_fund_news(fund_name)
        
        if not news_list:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                hot_keywords=[],
                key_news=[],
                sentiment_trend="stable"
            )
        
        # 统计情绪
        positive_count = sum(1 for n in news_list if n.sentiment == "positive")
        negative_count = sum(1 for n in news_list if n.sentiment == "negative")
        neutral_count = len(news_list) - positive_count - negative_count
        
        # 计算情绪分数
        total = len(news_list)
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0
        
        # 判断整体情绪
        if sentiment_score > 0.3:
            overall_sentiment = "bullish"
        elif sentiment_score < -0.3:
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"
        
        # 统计关键词
        keyword_count = {}
        for news in news_list:
            for kw in news.keywords:
                keyword_count[kw] = keyword_count.get(kw, 0) + 1
        
        hot_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 筛选重要新闻（情绪强烈且相关度高）
        key_news = [n for n in news_list if n.relevance > 0.7 and n.sentiment != "neutral"]
        key_news = sorted(key_news, key=lambda x: x.relevance, reverse=True)[:5]
        
        # 判断情绪趋势（简化版）
        if positive_count > negative_count * 2:
            sentiment_trend = "improving"
        elif negative_count > positive_count * 2:
            sentiment_trend = "worsening"
        else:
            sentiment_trend = "stable"
        
        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            sentiment_score=round(sentiment_score, 2),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            hot_keywords=hot_keywords,
            key_news=key_news,
            sentiment_trend=sentiment_trend
        )
    
    def get_market_hot_topics(self) -> List[Dict]:
        """
        获取市场热点话题
        """
        hot_topics = []
        
        try:
            # 尝试从东方财富获取热点
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1,
                'pz': 20,
                'po': 1,
                'np': 1,
                'fltt': 2,
                'invt': 2,
                'fid': 'f20',  # 按成交额排序
                'fs': 'm:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f20',
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and 'diff' in data['data']:
                for item in data['data']['diff'][:10]:
                    hot_topics.append({
                        'name': item.get('f14', ''),
                        'code': item.get('f12', ''),
                        'change_pct': item.get('f3', 0),
                        'amount': item.get('f20', 0),
                    })
        except Exception as e:
            print(f"获取热点失败: {e}")
        
        return hot_topics
    
    def generate_news_summary(self, fund_name: str) -> str:
        """
        生成新闻摘要
        """
        sentiment = self.analyze_fund_sentiment(fund_name)
        
        if not sentiment.key_news:
            return f"暂无{fund_name}相关重要新闻"
        
        summary_parts = []
        
        # 情绪概述
        sentiment_desc = {
            "bullish": "市场情绪偏多",
            "bearish": "市场情绪偏空",
            "neutral": "市场情绪中性"
        }
        summary_parts.append(f"【市场情绪】{sentiment_desc.get(sentiment.overall_sentiment, '中性')} "
                           f"(看多:{sentiment.positive_count} 看空:{sentiment.negative_count})")
        
        # 热点关键词
        if sentiment.hot_keywords:
            keywords_str = ", ".join([f"{kw}({count})" for kw, count in sentiment.hot_keywords[:5]])
            summary_parts.append(f"【热点关键词】{keywords_str}")
        
        # 重要新闻
        summary_parts.append("【重要新闻】")
        for i, news in enumerate(sentiment.key_news[:3], 1):
            emoji = "📈" if news.sentiment == "positive" else "📉" if news.sentiment == "negative" else "➖"
            summary_parts.append(f"  {i}. {emoji} {news.title}")
        
        return "\n".join(summary_parts)


if __name__ == "__main__":
    analyzer = FundNewsAnalyzer()
    
    # 测试分析
    fund_name = "中证半导体"
    print(f"正在分析 {fund_name} 的新闻舆情...")
    
    sentiment = analyzer.analyze_fund_sentiment(fund_name)
    
    print(f"\n情绪分析结果:")
    print(f"整体情绪: {sentiment.overall_sentiment} (分数: {sentiment.sentiment_score})")
    print(f"正面新闻: {sentiment.positive_count}")
    print(f"负面新闻: {sentiment.negative_count}")
    print(f"中性新闻: {sentiment.neutral_count}")
    print(f"情绪趋势: {sentiment.sentiment_trend}")
    
    print(f"\n热点关键词:")
    for kw, count in sentiment.hot_keywords[:5]:
        print(f"  {kw}: {count}次")
    
    print(f"\n重要新闻:")
    for news in sentiment.key_news[:3]:
        print(f"  [{news.sentiment}] {news.title}")
