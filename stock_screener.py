import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import json
from typing import List, Dict, Set
import time

load_dotenv()

fmp_key = os.getenv("FMP_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProfessionalStockScreener:
    """
    실전 기관투자자급 종목 발굴 시스템
    - Universe 기반 체계적 스크리닝
    - 4가지 검증된 투자 전략
    - CIO급 최종 통합 분석
    """
    
    def __init__(self):
        # Universe 캐시
        self._universe_cache = {}
        
        # 전략별 Universe 매핑
        self.strategy_config = {
            'hidden_gems': {
                'name': 'Hidden Gems (숨은 보석)',
                'universes': ['small_cap', 'mid_cap'],
                'description': '저평가 고성장 중소형주'
            },
            'deep_value': {
                'name': 'Deep Value (가치주)',
                'universes': ['large_cap', 'mid_cap', 'small_cap'],
                'description': '극단적 저평가 전 시총'
            },
            'quality_growth': {
                'name': 'Quality Growth (퀄리티 성장)',
                'universes': ['large_cap', 'mid_cap'],
                'description': '안정적 고수익 대중형주'
            },
            'momentum': {
                'name': 'Momentum (모멘텀)',
                'universes': ['large_cap', 'mid_cap'],
                'description': '강력한 상승세 전 시총'
            }
        }
    
    # ===== Universe 관리 =====
    
    def get_universe(self, universe_type: str) -> List[str]:
        """Universe 가져오기 (캐시 활용)"""
        
        if universe_type in self._universe_cache:
            return self._universe_cache[universe_type]
        
        print(f"   📥 {universe_type} Universe 로딩...")
        
        if universe_type == 'large_cap':
            symbols = self._get_large_cap()
        elif universe_type == 'mid_cap':
            symbols = self._get_mid_cap()
        elif universe_type == 'small_cap':
            symbols = self._get_small_cap()
        else:
            symbols = []
        
        self._universe_cache[universe_type] = symbols
        print(f"   ✅ {len(symbols)} 종목 로드됨")
        
        return symbols
    
    def _get_large_cap(self) -> List[str]:
        """대형주 (시총 100억+)"""
        
        # S&P 500 기반
        url = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={fmp_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return [stock['symbol'] for stock in data]
        
        # 대안: 직접 스크리닝
        return self._screener_query(
            market_cap_more=100000000000,
            limit=200
        )
    
    def _get_mid_cap(self) -> List[str]:
        """중형주 (시총 20억~100억)"""
        return self._screener_query(
            market_cap_more=2000000000,
            market_cap_lower=100000000000,
            limit=300
        )
    
    def _get_small_cap(self) -> List[str]:
        """소형주 (시총 3억~20억)"""
        return self._screener_query(
            market_cap_more=300000000,
            market_cap_lower=2000000000,
            limit=300
        )
    
    def _screener_query(self, market_cap_more=None, market_cap_lower=None, limit=100) -> List[str]:
        """FMP 스크리너 쿼리"""
        
        url = f"https://financialmodelingprep.com/api/v3/stock-screener"
        params = {
            'volumeMoreThan': 100000,
            'limit': limit,
            'apikey': fmp_key
        }
        
        if market_cap_more:
            params['marketCapMoreThan'] = market_cap_more
        if market_cap_lower:
            params['marketCapLowerThan'] = market_cap_lower
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return [stock['symbol'] for stock in data]
        except:
            return []
    
    # ===== 메인 스캔 로직 =====
    
    def scan_all_strategies(self, stocks_per_strategy=3):
        """전체 전략 스캔"""
        
        print("=" * 80)
        print("🏦 PROFESSIONAL STOCK SCREENER - Institutional Grade")
        print("=" * 80)
        print(f"⏰ 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        all_results = {}
        
        for strategy_key, config in self.strategy_config.items():
            print(f"\n{'='*80}")
            print(f"📊 전략: {config['name']}")
            print(f"📝 설명: {config['description']}")
            print(f"🎯 Universe: {', '.join(config['universes'])}")
            print(f"{'='*80}")
            
            # Universe 수집
            candidates = self._collect_candidates(config['universes'])
            print(f"\n총 후보: {len(candidates)} 종목")
            
            # 전략 실행
            picks = self._execute_strategy(strategy_key, candidates, stocks_per_strategy)
            all_results[strategy_key] = {
                'config': config,
                'picks': picks
            }
            
            print(f"✅ {len(picks)} 종목 선정 완료\n")
            time.sleep(1)  # API rate limit
        
        # AI 최종 분석
        print("\n" + "="*80)
        print("🤖 CIO 최종 통합 분석 중...")
        print("="*80)
        
        final_report = self._ai_final_analysis(all_results)
        
        return final_report
    
    def _collect_candidates(self, universes: List[str]) -> List[str]:
        """Universe에서 후보 수집"""
        
        all_symbols = set()
        
        for universe in universes:
            symbols = self.get_universe(universe)
            all_symbols.update(symbols)
        
        return list(all_symbols)
    
    def _execute_strategy(self, strategy_key: str, candidates: List[str], top_n: int) -> List[Dict]:
        """전략 실행"""
        
        if strategy_key == 'hidden_gems':
            return self._find_hidden_gems(candidates, top_n)
        elif strategy_key == 'deep_value':
            return self._find_deep_value(candidates, top_n)
        elif strategy_key == 'quality_growth':
            return self._find_quality_growth(candidates, top_n)
        elif strategy_key == 'momentum':
            return self._find_momentum(candidates, top_n)
        
        return []
    
    # ===== 전략 1: Hidden Gems =====
    
    def _find_hidden_gems(self, candidates: List[str], top_n: int) -> List[Dict]:
        """숨은 보석 발굴"""
        
        gems = []
        
        print("   분석 중: ", end="", flush=True)
        for i, symbol in enumerate(candidates[:100]):  # 처음 100개만
            if i % 10 == 0:
                print(".", end="", flush=True)
            
            try:
                analysis = self._analyze_hidden_gem(symbol)
                if analysis and analysis['is_gem']:
                    gems.append(analysis)
            except:
                continue
            
            time.sleep(0.1)  # Rate limit
        
        print(" 완료!")
        
        gems.sort(key=lambda x: x['score'], reverse=True)
        return gems[:top_n]
    
    def _analyze_hidden_gem(self, symbol: str) -> Dict:
        """Hidden Gem 분석"""
        
        quote = self._get_quote(symbol)
        if not quote:
            return None
        
        ratios = self._get_ratios(symbol)
        growth = self._get_growth(symbol)
        
        # 데이터 추출
        price = quote.get('price', 0)
        market_cap = quote.get('marketCap', 0)
        pe = quote.get('pe', 999)
        
        peg = ratios.get('pegRatio', 999) if ratios else 999
        revenue_growth = growth.get('revenueGrowth', 0) if growth else 0
        
        # 점수 계산
        score = 0
        reasons = []
        
        # 1. 고성장 (40점)
        if revenue_growth > 30:
            score += 40
            reasons.append(f"매출 성장 {revenue_growth:.1f}%")
        elif revenue_growth > 20:
            score += 30
            reasons.append(f"매출 성장 {revenue_growth:.1f}%")
        elif revenue_growth > 10:
            score += 20
        
        # 2. 저PEG (30점)
        if 0 < peg < 1:
            score += 30
            reasons.append(f"PEG {peg:.2f} (저평가)")
        elif peg < 1.5:
            score += 20
            reasons.append(f"PEG {peg:.2f}")
        elif peg < 2:
            score += 10
        
        # 3. 중소형주 (20점)
        if market_cap < 5e9:
            score += 20
            reasons.append("소형주")
        elif market_cap < 20e9:
            score += 15
            reasons.append("중소형주")
        elif market_cap < 50e9:
            score += 10
        
        # 4. 적정 PE (10점)
        if 10 < pe < 25:
            score += 10
            reasons.append(f"PE {pe:.1f}")
        elif 5 < pe < 35:
            score += 5
        
        is_gem = score >= 60
        
        return {
            'symbol': symbol,
            'name': quote.get('name', 'N/A'),
            'price': price,
            'market_cap': market_cap,
            'pe': pe,
            'peg': peg,
            'revenue_growth': revenue_growth,
            'score': score,
            'is_gem': is_gem,
            'reasons': reasons,
            'category': 'Hidden Gem'
        }
    
    # ===== 전략 2: Deep Value =====
    
    def _find_deep_value(self, candidates: List[str], top_n: int) -> List[Dict]:
        """가치주 발굴"""
        
        value_stocks = []
        
        print("   분석 중: ", end="", flush=True)
        for i, symbol in enumerate(candidates[:100]):
            if i % 10 == 0:
                print(".", end="", flush=True)
            
            try:
                analysis = self._analyze_value(symbol)
                if analysis and analysis['is_value']:
                    value_stocks.append(analysis)
            except:
                continue
            
            time.sleep(0.1)
        
        print(" 완료!")
        
        value_stocks.sort(key=lambda x: x['score'], reverse=True)
        return value_stocks[:top_n]
    
    def _analyze_value(self, symbol: str) -> Dict:
        """가치주 분석 (Graham 방식)"""
        
        quote = self._get_quote(symbol)
        if not quote:
            return None
        
        ratios = self._get_ratios(symbol)
        
        pe = quote.get('pe', 999)
        pb = ratios.get('priceToBookRatio', 999) if ratios else 999
        roe = ratios.get('roe', 0) if ratios else 0
        div_yield = ratios.get('dividendYield', 0) if ratios else 0
        
        score = 0
        reasons = []
        
        # 1. P/B (30점)
        if pb < 1:
            score += 30
            reasons.append(f"P/B {pb:.2f} (장부가 이하)")
        elif pb < 1.5:
            score += 20
            reasons.append(f"P/B {pb:.2f}")
        elif pb < 2:
            score += 10
        
        # 2. P/E (30점)
        if 5 < pe < 12:
            score += 30
            reasons.append(f"P/E {pe:.1f} (저평가)")
        elif pe < 18:
            score += 20
            reasons.append(f"P/E {pe:.1f}")
        elif pe < 25:
            score += 10
        
        # 3. ROE (20점)
        if roe > 15:
            score += 20
            reasons.append(f"ROE {roe:.1f}%")
        elif roe > 10:
            score += 15
        elif roe > 5:
            score += 10
        
        # 4. 배당 (20점)
        if div_yield > 3:
            score += 20
            reasons.append(f"배당 {div_yield:.1f}%")
        elif div_yield > 2:
            score += 15
        elif div_yield > 1:
            score += 10
        
        is_value = score >= 60
        
        return {
            'symbol': symbol,
            'name': quote.get('name', 'N/A'),
            'price': quote.get('price', 0),
            'pe': pe,
            'pb': pb,
            'roe': roe,
            'dividend': div_yield,
            'score': score,
            'is_value': is_value,
            'reasons': reasons,
            'category': 'Deep Value'
        }
    
    # ===== 전략 3: Quality Growth =====
    
    def _find_quality_growth(self, candidates: List[str], top_n: int) -> List[Dict]:
        """퀄리티 성장주 발굴"""
        
        quality_stocks = []
        
        print("   분석 중: ", end="", flush=True)
        for i, symbol in enumerate(candidates[:100]):
            if i % 10 == 0:
                print(".", end="", flush=True)
            
            try:
                analysis = self._analyze_quality(symbol)
                if analysis and analysis['is_quality']:
                    quality_stocks.append(analysis)
            except:
                continue
            
            time.sleep(0.1)
        
        print(" 완료!")
        
        quality_stocks.sort(key=lambda x: x['score'], reverse=True)
        return quality_stocks[:top_n]
    
    def _analyze_quality(self, symbol: str) -> Dict:
        """퀄리티 분석 (Lynch/Buffett 방식)"""
        
        quote = self._get_quote(symbol)
        if not quote:
            return None
        
        ratios = self._get_ratios(symbol)
        growth = self._get_growth(symbol)
        
        roe = ratios.get('roe', 0) if ratios else 0
        roic = ratios.get('roic', 0) if ratios else 0
        revenue_growth = growth.get('revenueGrowth', 0) if growth else 0
        
        score = 0
        reasons = []
        
        # 1. ROE (35점)
        if roe > 25:
            score += 35
            reasons.append(f"ROE {roe:.1f}% (탁월)")
        elif roe > 20:
            score += 25
            reasons.append(f"ROE {roe:.1f}%")
        elif roe > 15:
            score += 15
        
        # 2. 일관된 성장 (35점)
        if revenue_growth > 20:
            score += 35
            reasons.append(f"매출 성장 {revenue_growth:.1f}%")
        elif revenue_growth > 15:
            score += 25
        elif revenue_growth > 10:
            score += 15
        
        # 3. ROIC (30점)
        if roic > 20:
            score += 30
            reasons.append(f"ROIC {roic:.1f}%")
        elif roic > 15:
            score += 20
        elif roic > 10:
            score += 10
        
        is_quality = score >= 60
        
        return {
            'symbol': symbol,
            'name': quote.get('name', 'N/A'),
            'price': quote.get('price', 0),
            'roe': roe,
            'roic': roic,
            'revenue_growth': revenue_growth,
            'score': score,
            'is_quality': is_quality,
            'reasons': reasons,
            'category': 'Quality Growth'
        }
    
    # ===== 전략 4: Momentum =====
    
    def _find_momentum(self, candidates: List[str], top_n: int) -> List[Dict]:
        """모멘텀주 발굴"""
        
        momentum_stocks = []
        
        print("   분석 중: ", end="", flush=True)
        for i, symbol in enumerate(candidates[:100]):
            if i % 10 == 0:
                print(".", end="", flush=True)
            
            try:
                analysis = self._analyze_momentum(symbol)
                if analysis and analysis['has_momentum']:
                    momentum_stocks.append(analysis)
            except:
                continue
            
            time.sleep(0.1)
        
        print(" 완료!")
        
        momentum_stocks.sort(key=lambda x: x['score'], reverse=True)
        return momentum_stocks[:top_n]
    
    def _analyze_momentum(self, symbol: str) -> Dict:
        """모멘텀 분석 (O'Neil 방식)"""
        
        quote = self._get_quote(symbol)
        if not quote:
            return None
        
        price = quote.get('price', 0)
        change = quote.get('changesPercentage', 0)
        year_high = quote.get('yearHigh', 0)
        year_low = quote.get('yearLow', 0)
        
        # 52주 고가 근접도
        high_proximity = (price / year_high * 100) if year_high > 0 else 0
        
        score = 0
        reasons = []
        
        # 1. 최근 상승률 (40점)
        if change > 10:
            score += 40
            reasons.append(f"상승 {change:.1f}%")
        elif change > 5:
            score += 30
        elif change > 2:
            score += 20
        
        # 2. 52주 고가 근접 (40점)
        if high_proximity > 95:
            score += 40
            reasons.append("52주 신고가 근접")
        elif high_proximity > 90:
            score += 30
        elif high_proximity > 85:
            score += 20
        
        # 3. 연간 상승폭 (20점)
        if year_high > 0 and year_low > 0:
            year_range = (year_high - year_low) / year_low * 100
            if year_range > 100:
                score += 20
                reasons.append(f"연중 {year_range:.0f}% 상승")
            elif year_range > 50:
                score += 15
            elif year_range > 30:
                score += 10
        
        has_momentum = score >= 60
        
        return {
            'symbol': symbol,
            'name': quote.get('name', 'N/A'),
            'price': price,
            'change': change,
            'high_proximity': high_proximity,
            'score': score,
            'has_momentum': has_momentum,
            'reasons': reasons,
            'category': 'Momentum'
        }
    
    # ===== 데이터 헬퍼 함수 =====
    
    def _get_quote(self, symbol: str) -> Dict:
        """시세 정보"""
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data[0] if data else None
        except:
            return None
    
    def _get_ratios(self, symbol: str) -> Dict:
        """재무 비율"""
        try:
            url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?limit=1&apikey={fmp_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data[0] if data else None
        except:
            return None
    
    def _get_growth(self, symbol: str) -> Dict:
        """성장률"""
        try:
            url = f"https://financialmodelingprep.com/api/v3/financial-growth/{symbol}?limit=1&apikey={fmp_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data:
                return {
                    'revenueGrowth': data[0].get('revenueGrowth', 0) * 100
                }
            return None
        except:
            return None
    
    # ===== AI 최종 분석 =====
    
    def _ai_final_analysis(self, all_results: Dict) -> Dict:
        """CIO급 통합 분석"""
        
        # 결과 요약
        summary = "=== 전문가급 멀티전략 스크리닝 결과 ===\n\n"
        
        for strategy_key, data in all_results.items():
            config = data['config']
            picks = data['picks']
            
            summary += f"\n## {config['name']}\n"
            summary += f"Universe: {', '.join(config['universes'])}\n"
            summary += f"발굴: {len(picks)} 종목\n\n"
            
            for i, stock in enumerate(picks, 1):
                summary += f"{i}. {stock['symbol']} - {stock['name']}\n"
                summary += f"   가격: ${stock['price']:.2f}\n"
                summary += f"   점수: {stock['score']}/100\n"
                summary += f"   특징: {', '.join(stock.get('reasons', []))}\n"
        
        # GPT-4o CIO 분석
        prompt = f"""
당신은 30년 경력의 CIO(최고투자책임자)입니다.

4가지 전문 전략으로 발굴된 종목들을 검토하고 실행 가능한 투자 계획을 수립하세요:

{summary}

**CIO 최종 리포트:**

1. Executive Summary (핵심 요약)
   - 시장 환경 한 줄
   - 핵심 기회 한 줄

2. 전략별 평가
   - 각 전략의 강점
   - 현재 시장에서의 적합성

3. Top 5 Conviction Picks
   - 전 전략 통틀어 최고 5개
   - 각각: 종목명, 카테고리, 선정 이유, 목표 수익률

4. 포트폴리오 구성 제안
   - 각 전략 비중 (%)
   - 리스크 관리 방안

5. 실행 계획
   - 1주차 액션
   - 모니터링 포인트

전문적이고 실행 가능하게 작성하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'strategies': all_results,
            'cio_report': response.choices[0].message.content
        }


# ===== 실행 =====
if __name__ == "__main__":
    screener = ProfessionalStockScreener()
    
    # 전체 스캔
    report = screener.scan_all_strategies(stocks_per_strategy=3)
    
    # 결과 출력
    print("\n" + "="*80)
    print("📊 CIO 최종 투자 리포트")
    print("="*80)
    print(report['cio_report'])
    
    # 저장
    filename = f"stock_discovery_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 리포트 저장: {filename}")
    print(f"⏰ 완료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")