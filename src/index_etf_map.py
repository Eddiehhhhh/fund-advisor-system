"""
指数 ↔ ETF 映射表模块

集中管理主流指数与对应 ETF 代码的映射关系。
从 data_fetcher.py 中剥离出来的独立模块，消除三处重复定义。

使用方式：
    from index_etf_map import get_etf_code, get_index_name, list_indices_by_category

    code = get_etf_code('000300')  # -> '510300'
    name = get_index_name('000300')  # -> '沪深300'
"""

from typing import Dict, Optional, List

# ---------------------------------------------------------------------------
# 权威映射表（唯一数据源）
# ---------------------------------------------------------------------------
# 每项：指数代码 → {
#   name:        中文名称
#   category:    分类（宽基 / 行业-xxx / 海外）
#   etf_code:    场内 ETF 代码（用于行情、资金流向等）
#   fund_code:   场外基金代码（用于天天基金历史净值 API）
#   exchange:    交易所
# }

INDEX_MAP: Dict[str, dict] = {
    # === 宽基 ===
    '000300': {
        'name': '沪深300',
        'category': '宽基',
        'etf_code': '510300',     # 华泰柏瑞
        'fund_code': '110020',    # 易方达
        'exchange': 'SSE',
    },
    '000905': {
        'name': '中证500',
        'category': '宽基',
        'etf_code': '510500',     # 南方
        'fund_code': '160119',    # 南方
        'exchange': 'SSE',
    },
    '399006': {
        'name': '创业板指',
        'category': '宽基',
        'etf_code': '159915',     # 易方达
        'fund_code': '110026',    # 易方达
        'exchange': 'SZSE',
    },
    '000688': {
        'name': '科创50',
        'category': '宽基',
        'etf_code': '588000',     # 华夏
        'fund_code': '011612',    # 华夏
        'exchange': 'SSE',
    },
    '000016': {
        'name': '上证50',
        'category': '宽基',
        'etf_code': '510050',     # 华夏
        'fund_code': '110003',    # 易方达
        'exchange': 'SSE',
    },
    '000852': {
        'name': '中证1000',
        'category': '宽基',
        'etf_code': '512100',     # 华夏南方512100（参考）
        'fund_code': '159845',    # 华夏
        'exchange': 'SSE',
    },
    # === 行业 ===
    '399997': {
        'name': '中证白酒',
        'category': '行业-消费',
        'etf_code': '512690',     # 鹏华
        'fund_code': '160632',    # 鹏华
        'exchange': 'SSE',
    },
    '399989': {
        'name': '中证医疗',
        'category': '行业-医药',
        'etf_code': '512170',     # 华宝
        'fund_code': '162412',    # 华宝
        'exchange': 'SSE',
    },
    '399808': {
        'name': '中证新能源',
        'category': '行业-新能源',
        'etf_code': '516160',     # 华夏南方
        'fund_code': '164905',    # 华安
        'exchange': 'SSE',
    },
    'H30184': {
        'name': '中证半导体',
        'category': '行业-科技',
        'etf_code': '512480',     # 国泰
        'fund_code': '008282',    # 国联安
        'exchange': 'SSE',
    },
    '399967': {
        'name': '中证军工',
        'category': '行业-军工',
        'etf_code': '512660',     # 国泰
        'fund_code': '502003',    # 易方达
        'exchange': 'SSE',
    },
    '399986': {
        'name': '中证银行',
        'category': '行业-金融',
        'etf_code': '512800',     # 华宝
        'fund_code': '160631',    # 鹏华
        'exchange': 'SSE',
    },
    '399975': {
        'name': '证券公司',
        'category': '行业-金融',
        'etf_code': '512880',     # 国泰
        'fund_code': '502010',    # 易方达
        'exchange': 'SSE',
    },
    '931775': {
        'name': '中证房地产',
        'category': '行业-地产',
        'etf_code': '512200',     # 建信
        'fund_code': '160628',    # 鹏华
        'exchange': 'SSE',
    },
    '930050': {
        'name': '中证人工智能',
        'category': '行业-科技',
        'etf_code': '515070',     # 华宝
        'fund_code': '008585',    # 融通
        'exchange': 'SSE',
    },
    'H30233': {
        'name': '中证传媒',
        'category': '行业-传媒',
        'etf_code': '512980',     # 易方达
        'fund_code': '004752',    # 广发
        'exchange': 'SSE',
    },
    # === 海外 ===
    'NDX': {
        'name': '纳斯达克100',
        'category': '海外',
        'etf_code': None,
        'fund_code': '040046',    # 华安
        'exchange': 'NASDAQ',
    },
    'SPX': {
        'name': '标普500',
        'category': '海外',
        'etf_code': None,
        'fund_code': '050025',    # 博时
        'exchange': 'NYSE',
    },
    'HSI': {
        'name': '恒生指数',
        'category': '海外',
        'etf_code': None,
        'fund_code': '164705',    # 汇添富
        'exchange': 'HKEX',
    },
}

# ---------------------------------------------------------------------------
# 反向查询：ETF 代码 → 指数代码
# ---------------------------------------------------------------------------
ETF_TO_INDEX: Dict[str, str] = {
    info['etf_code']: code
    for code, info in INDEX_MAP.items()
    if info['etf_code']
}

FUND_CODE_TO_INDEX: Dict[str, str] = {
    info['fund_code']: code
    for code, info in INDEX_MAP.items()
    if info['fund_code']
}


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

def get_index_info(index_code: str) -> Optional[dict]:
    """获取指数完整信息，不存在返回 None"""
    return INDEX_MAP.get(index_code)


def get_etf_code(index_code: str) -> Optional[str]:
    """指数代码 → 场内 ETF 代码（可能 None，如海外指数）"""
    info = INDEX_MAP.get(index_code)
    return info['etf_code'] if info else None


def get_fund_code(index_code: str) -> Optional[str]:
    """指数代码 → 场外基金代码（历史净值 API 用）"""
    info = INDEX_MAP.get(index_code)
    return info['fund_code'] if info else None


def get_index_name(index_code: str) -> Optional[str]:
    """指数代码 → 中文名称"""
    info = INDEX_MAP.get(index_code)
    return info['name'] if info else None


def get_category(index_code: str) -> Optional[str]:
    """指数代码 → 分类（宽基 / 行业-xxx / 海外）"""
    info = INDEX_MAP.get(index_code)
    return info['category'] if info else None


def list_indices_by_category(category: str) -> List[str]:
    """按分类返回指数代码列表。category 支持模糊匹配（如 '行业' 会匹配所有行业子类）"""
    return [
        code for code, info in INDEX_MAP.items()
        if info['category'] == category or info['category'].startswith(category)
    ]


def list_all_indices() -> List[str]:
    """返回所有指数代码"""
    return list(INDEX_MAP.keys())


def get_index_code_by_etf(etf_code: str) -> Optional[str]:
    """ETF 代码 → 指数代码 (反向查询)"""
    return ETF_TO_INDEX.get(etf_code)


def get_index_code_by_fund(fund_code: str) -> Optional[str]:
    """场外基金代码 → 指数代码 (反向查询)"""
    return FUND_CODE_TO_INDEX.get(fund_code)


def search_index(keyword: str) -> List[dict]:
    """按关键词搜索指数（匹配代码或中文名），返回匹配结果列表"""
    keyword = keyword.upper()
    results = []
    for code, info in INDEX_MAP.items():
        if keyword in code.upper() or keyword in info['name']:
            results.append({'code': code, **info})
    return results


if __name__ == '__main__':
    # 简单自测
    print(f"共 {len(INDEX_MAP)} 个指数")
    print(f"\n宽基: {list_indices_by_category('宽基')}")
    print(f"行业: {list_indices_by_category('行业')}")
    print(f"海外: {list_indices_by_category('海外')}")
    print(f"\n沪深300 ETF: {get_etf_code('000300')}")
    print(f"半导体 基金: {get_fund_code('H30184')}")
    print(f"ETF 510300 → 指数: {get_index_code_by_etf('510300')}")
    print(f"搜索'半导体': {search_index('半导体')}")
