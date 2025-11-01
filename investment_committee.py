import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import json
from typing import Dict, List

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InvestmentCommittee:
    """
    기관투자자급 투자위원회 - 실전 버전
    - 실시간 계좌 동기화
    - 보유 종목 중심 분석
    - 5개 전문팀 협업
    """
    
    def __init__(self, portfolio_manager, stock_screener):
        self.pm = portfolio_manager
        self.screener = stock_screener
        
        # KIS 연동
        from kis_connector import KISConnector
        self.kis = KISConnector()
        
        # 팀 초기화
        self.market_intel = MarketIntelligenceTeam()
        self.risk_mgmt = RiskManagementTeam()
        self.technical = TechnicalAnalysisTeam(stock_screener)
        self.fundamental = FundamentalAnalysisTeam()
    
    def conduct_investment_meeting(self):
        """투자위원회 개최"""
        
        print("=" * 80)
        print("🏛️  INVESTMENT COMMITTEE MEETING")
        print("=" * 80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)
        
        # ===== STEP 1: 실시간 계좌 동기화 =====
        print("\n📡 STEP 1: 실시간 계좌 동기화")
        print("─" * 80)
        
        try:
            real_data = self.kis.parse_portfolio()
            self.kis.sync_to_portfolio_manager(self.pm)
            
            print(f"✅ 동기화 완료")
            print(f"   보유 종목: {len(real_data['holdings'])}개")
            print(f"   총 평가액: ${real_data['total_value']:,.2f}\n")
            
            # 보유 종목 목록 출력
            for symbol, data in real_data['holdings'].items():
                print(f"   - {symbol}: {data['shares']:.4f}주 (${data['current_value']:.2f})")
            
            synced = True
            
        except Exception as e:
            print(f"⚠️  동기화 실패: {e}")
            print("저장된 데이터로 진행\n")
            real_data = None
            synced = False
        
        # 현재 포트폴리오 (최신 데이터)
        current = self.pm.get_current_value()
        
        # ===== STEP 2: 팀별 분석 =====
        
        # Team 1: Market Intelligence
        print("\n📰 STEP 2A: MARKET INTELLIGENCE TEAM")
        print("─" * 80)
        market_report = self.market_intel.analyze_with_holdings(
            current['holdings'],  # 실제 보유 종목들
            real_data['holdings'] if real_data else {}
        )
        
        # Team 2: Risk Management
        print("\n⚠️  STEP 2B: RISK MANAGEMENT TEAM")
        print("─" * 80)
        risk_report = self.risk_mgmt.analyze_with_holdings(
            current,
            real_data['holdings'] if real_data else {}
        )
        
        # Team 3: Technical Analysis (새 종목 발굴)
        print("\n📊 STEP 2C: TECHNICAL ANALYSIS TEAM")
        print("─" * 80)
        technical_report = self.technical.discover_opportunities()
        
        # Team 4: Fundamental Analysis
        print("\n📈 STEP 2D: FUNDAMENTAL ANALYSIS TEAM")
        print("─" * 80)
        fundamental_report = self.fundamental.analyze_all(
            current['holdings'],  # 보유 종목
            technical_report['discoveries']  # 발굴 종목
        )
        
        # ===== STEP 3: CIO 최종 결정 =====
        print("\n👔 STEP 3: CIO 최종 의사결정")
        print("=" * 80)
        
        final_decision = self._cio_comprehensive_decision(
            current,
            market_report,
            risk_report,
            technical_report,
            fundamental_report
        )
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'synced': synced,
            'portfolio': current,
            'market_intelligence': market_report,
            'risk_management': risk_report,
            'technical_analysis': technical_report,
            'fundamental_analysis': fundamental_report,
            'cio_decision': final_decision
        }
    
    def _cio_comprehensive_decision(self, portfolio, market, risk, technical, fundamental):
        """CIO 종합 의사결정"""
        
        # 보유 종목 요약
        holdings_summary = "## 현재 보유 종목\n\n"
        for holding in portfolio['holdings']:
            symbol = holding['symbol']
            holdings_summary += f"""
### {symbol}
- 보유: {holding['shares']:.4f}주
- 평가액: ${holding['current_value']:.2f}
- 수익률: {holding['profit_pct']:+.2f}%

**Market Intelligence 분석:**
{market['holdings_analysis'].get(symbol, 'N/A')}

**Fundamental 분석:**
{fundamental['holdings_analysis'].get(symbol, 'N/A')}

"""
        
        # 발굴 종목 요약
        discoveries_summary = "## 발굴 종목\n\n"
        for pick in technical['discoveries'][:5]:
            symbol = pick['symbol']
            discoveries_summary += f"""
### {symbol}
- 가격: ${pick['price']:.2f}
- 전략: {pick['category']}
- 점수: {pick['score']}/100

**Fundamental 분석:**
{fundamental['discoveries_analysis'].get(symbol, 'N/A')}

"""
        
        prompt = f"""
당신은 30년 경력의 CIO입니다.

투자위원회 전체 보고가 완료되었습니다.
**실제 계좌 데이터**를 기반으로 최종 결정을 내리세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{holdings_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Risk Management 보고

**포트폴리오 리스크:**
- 리스크 점수: {risk['risk_score']}/100
- 집중도: {risk.get('concentration', {}).get('max_single_stock', 0):.1f}%
- 주요 리스크: {', '.join(risk['main_risks'])}

**권고사항:**
{risk['recommendations']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Market Intelligence 보고

**거시경제 환경:**
{market['macro_environment']}

**시장 심리:**
{market['market_sentiment']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{discoveries_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CIO 최종 결정서

### 1. Executive Summary (3줄)
- 현재 포트폴리오 평가
- 핵심 투자 방향
- 예상 효과

### 2. 보유 종목별 결정

각 보유 종목에 대해:
- **[종목명]**: 보유유지 / 일부매도(%) / 전량매도
- **근거**: 모든 팀 분석 종합
- **실행 타이밍**: 즉시 / 관망

### 3. 신규 매수 결정

발굴 종목 중:
- **[종목명]**: 매수 / 관망
- **근거**: 모든 팀 분석 종합
- **금액**: 구체적 금액
- **비중**: 목표 포트폴리오 비중

### 4. 리밸런싱 후 포트폴리오
- 각 종목 비중
- 섹터 분산
- 예상 리스크 점수

### 5. 실행 계획
1단계: [즉시]
2단계: [1주내]
3단계: [모니터링]

### 6. 리스크 관리
- 주요 리스크
- 대응 방안
- 손절 기준

**중요:**
- 모든 결정에 팀별 근거 명시
- 보수적이고 실행 가능하게
- 구체적 수치 제시
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000
        )
        
        return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════
# TEAM 1: Market Intelligence (재설계)
# ═══════════════════════════════════════════════════════════

class MarketIntelligenceTeam:
    """시장 정보 팀 - 보유 종목 중심"""
    
    def analyze_with_holdings(self, holdings_list, real_data):
        """보유 종목 중심 분석"""
        
        print("   💼 Team Lead: Sarah Chen")
        print("   📋 거시경제 + 보유종목 뉴스 분석\n")
        
        # 1. 거시경제
        macro = self._analyze_macro()
        print("   ✅ 거시경제 분석 완료")
        
        # 2. 시장 심리
        sentiment = self._analyze_market_sentiment()
        print("   ✅ 시장 심리 분석 완료")
        
        # 3. 보유 종목 각각 뉴스 분석
        holdings_analysis = {}
        
        print(f"   📰 보유 종목 뉴스 분석 중...")
        for holding in holdings_list:
            symbol = holding['symbol']
            analysis = self._deep_news_analysis(symbol)
            holdings_analysis[symbol] = analysis
            print(f"      - {symbol} 완료")
        
        return {
            'macro_environment': macro,
            'market_sentiment': sentiment,
            'holdings_analysis': holdings_analysis
        }
    
    def _analyze_macro(self):
        """거시경제"""
        
        prompt = """
현재 투자 환경 분석 (웹 검색 활용):

1. 미국 경제: 금리, 인플레이션, 고용
2. 정치: 주요 정책, 선거
3. 글로벌: 지정학적 리스크
4. 섹터: 강세/약세 섹터

종합 평가: 긍정/중립/부정

200단어 이내, 투자 관점.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        return response.choices[0].message.content
    
    def _analyze_market_sentiment(self):
        """시장 심리"""
        
        prompt = """
웹 검색으로 현재 시장 심리 분석:

1. VIX 지수 수준
2. 투자자 심리 (공포/탐욕)
3. 주요 우려 사항
4. 기회 요인

100단어 이내.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        
        return response.choices[0].message.content
    
    def _deep_news_analysis(self, symbol):
        """종목별 심층 뉴스"""
        
        prompt = f"""
{symbol} 심층 뉴스 분석 (웹 검색):

1. 최근 1주일 주요 뉴스 3개
2. 시장 반응 (주가 변동)
3. 애널리스트 의견
4. 주요 리스크/기회
5. 투자 의견: 매수/보유/매도

**투자위원회 보고용, 150단어.**
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════
# TEAM 2: Risk Management (재설계)
# ═══════════════════════════════════════════════════════════

class RiskManagementTeam:
    """리스크 관리 팀 - 보유 종목 중심"""
    
    def analyze_with_holdings(self, portfolio, real_data):
        """보유 종목 리스크 분석"""
        
        print("   💼 Team Lead: Michael Torres")
        print("   📋 포트폴리오 리스크 분석\n")
        
        holdings = portfolio['holdings']
        total_value = portfolio['stock_value']
        
        # 1. 집중도 리스크
        concentration = self._analyze_concentration(holdings, total_value)
        print("   ✅ 집중도 분석 완료")
        
        # 2. 변동성 리스크
        volatility = self._analyze_volatility(holdings)
        print("   ✅ 변동성 분석 완료")
        
        # 3. 섹터 리스크 (종목별로)
        sector_risk = self._analyze_sector_risk(holdings)
        print("   ✅ 섹터 리스크 완료")
        
        # 4. 종합 리스크 점수
        risk_score = self._calculate_comprehensive_risk(
            concentration, 
            volatility, 
            sector_risk
        )
        
        # 5. 주요 리스크
        main_risks = self._identify_risks(
            portfolio, 
            concentration, 
            volatility,
            sector_risk
        )
        
        # 6. 권고사항
        recommendations = self._generate_recommendations(
            risk_score,
            main_risks,
            holdings
        )
        
        return {
            'risk_score': risk_score,
            'concentration': concentration,
            'volatility': volatility,
            'sector_risk': sector_risk,
            'main_risks': main_risks,
            'recommendations': recommendations
        }
    
    def _analyze_concentration(self, holdings, total_value):
        """집중도"""
        
        if total_value == 0 or not holdings:
            return {'status': 'No holdings'}
        
        # 종목별 비중
        weights = {}
        for h in holdings:
            weight = (h['current_value'] / total_value * 100)
            weights[h['symbol']] = weight
        
        max_weight = max(weights.values()) if weights else 0
        
        # 상위 3개
        sorted_holdings = sorted(holdings, key=lambda x: x['current_value'], reverse=True)
        top3_value = sum([h['current_value'] for h in sorted_holdings[:3]])
        top3_weight = (top3_value / total_value * 100) if total_value > 0 else 0
        
        return {
            'weights': weights,
            'max_single_stock': max_weight,
            'top3_concentration': top3_weight,
            'num_stocks': len(holdings)
        }
    
    def _analyze_volatility(self, holdings):
        """변동성"""
        
        if not holdings:
            return {'status': 'No holdings'}
        
        profit_pcts = [abs(h['profit_pct']) for h in holdings]
        avg_volatility = sum(profit_pcts) / len(profit_pcts) if profit_pcts else 0
        max_loss = min([h['profit_pct'] for h in holdings]) if holdings else 0
        max_gain = max([h['profit_pct'] for h in holdings]) if holdings else 0
        
        return {
            'avg_volatility': avg_volatility,
            'max_loss': max_loss,
            'max_gain': max_gain
        }
    
    def _analyze_sector_risk(self, holdings):
        """섹터 리스크 (웹 검색)"""
        
        if not holdings:
            return {'status': 'No holdings'}
        
        symbols = [h['symbol'] for h in holdings[:3]]  # 상위 3개만
        
        prompt = f"""
다음 종목들의 섹터 분석 (웹 검색):

{', '.join(symbols)}

1. 각 종목의 섹터
2. 섹터 집중도
3. 섹터별 리스크
4. 분산 필요성

100단어 이내.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        
        return response.choices[0].message.content
    
    def _calculate_comprehensive_risk(self, concentration, volatility, sector_risk):
        """종합 리스크 점수"""
        
        score = 0
        
        # 집중도 (40점)
        if isinstance(concentration, dict) and 'max_single_stock' in concentration:
            max_weight = concentration['max_single_stock']
            if max_weight > 50:
                score += 40
            elif max_weight > 30:
                score += 25
            elif max_weight > 20:
                score += 15
            elif max_weight > 10:
                score += 5
        
        # 변동성 (40점)
        if isinstance(volatility, dict) and 'avg_volatility' in volatility:
            vol = volatility['avg_volatility']
            if vol > 30:
                score += 40
            elif vol > 20:
                score += 25
            elif vol > 10:
                score += 15
            elif vol > 5:
                score += 5
        
        # 분산 부족 (20점)
        if isinstance(concentration, dict) and 'num_stocks' in concentration:
            num = concentration['num_stocks']
            if num == 1:
                score += 20
            elif num == 2:
                score += 15
            elif num < 5:
                score += 10
        
        return min(score, 100)
    
    def _identify_risks(self, portfolio, concentration, volatility, sector_risk):
        """주요 리스크"""
        
        risks = []
        
        if isinstance(concentration, dict):
            max_weight = concentration.get('max_single_stock', 0)
            if max_weight > 50:
                risks.append(f"극단적 집중도 ({max_weight:.0f}%)")
            elif max_weight > 30:
                risks.append(f"높은 집중도 ({max_weight:.0f}%)")
            
            if concentration.get('num_stocks', 0) < 3:
                risks.append("분산 부족")
        
        if isinstance(volatility, dict):
            max_loss = volatility.get('max_loss', 0)
            if max_loss < -20:
                risks.append(f"큰 손실 종목 ({max_loss:.0f}%)")
            elif max_loss < -10:
                risks.append(f"손실 종목 존재 ({max_loss:.0f}%)")
        
        if portfolio['cash'] < portfolio['total_value'] * 0.05:
            risks.append("현금 부족")
        
        return risks if risks else ["리스크 양호"]
    
    def _generate_recommendations(self, risk_score, risks, holdings):
        """권고사항"""
        
        recs = []
        
        if risk_score > 70:
            recs.append("⚠️  높은 리스크 - 즉시 리밸런싱 필요")
        elif risk_score > 50:
            recs.append("주의 - 리밸런싱 검토")
        else:
            recs.append("리스크 양호")
        
        # 구체적 권고
        for risk in risks:
            if "집중도" in risk:
                recs.append("→ 비중 분산 필요")
            if "분산 부족" in risk:
                recs.append("→ 종목 수 확대")
            if "손실" in risk:
                recs.append("→ 손절 검토")
            if "현금 부족" in risk:
                recs.append("→ 현금 확보")
        
        return "\n".join(recs)


# ═══════════════════════════════════════════════════════════
# TEAM 3: Technical Analysis (기존 유지)
# ═══════════════════════════════════════════════════════════

class TechnicalAnalysisTeam:
    """기술 분석 팀"""
    
    def __init__(self, screener):
        self.screener = screener
    
    def discover_opportunities(self):
        """기회 발굴"""
        
        print("   💼 Team Lead: David Kim")
        print("   📋 시장 스캔 중 (5-10분)...\n")
        
        results = self.screener.scan_all_strategies(stocks_per_strategy=2)
        
        # 모든 발굴 종목 수집
        all_discoveries = []
        for strategy_key, data in results['strategies'].items():
            for pick in data['picks']:
                pick['strategy'] = data['config']['name']
                all_discoveries.append(pick)
        
        print(f"   ✅ {len(all_discoveries)}개 종목 발굴 완료")
        
        return {
            'full_results': results,
            'discoveries': all_discoveries
        }


# ═══════════════════════════════════════════════════════════
# TEAM 4: Fundamental Analysis (재설계)
# ═══════════════════════════════════════════════════════════

class FundamentalAnalysisTeam:
    """펀더멘털 분석 팀"""
    
    def analyze_all(self, holdings_list, discovered_stocks):
        """보유 + 발굴 종목 모두 분석"""
        
        print("   💼 Team Lead: Emily Watson")
        print("   📋 펀더멘털 분석\n")
        
        # 1. 보유 종목 분석
        holdings_analysis = {}
        
        print("   보유 종목 분석 중...")
        for holding in holdings_list[:5]:  # 최대 5개
            symbol = holding['symbol']
            analysis = self._fundamental_analysis(symbol, is_holding=True)
            holdings_analysis[symbol] = analysis
            print(f"      - {symbol} 완료")
        
        # 2. 발굴 종목 분석
        discoveries_analysis = {}
        
        print("   발굴 종목 분석 중...")
        for stock in discovered_stocks[:5]:  # 최대 5개
            symbol = stock['symbol']
            analysis = self._fundamental_analysis(symbol, is_holding=False)
            discoveries_analysis[symbol] = analysis
            print(f"      - {symbol} 완료")
        
        return {
            'holdings_analysis': holdings_analysis,
            'discoveries_analysis': discoveries_analysis
        }
    
    def _fundamental_analysis(self, symbol, is_holding):
        """종목별 펀더멘털"""
        
        context = "현재 보유 중" if is_holding else "매수 검토 대상"
        
        prompt = f"""
{symbol} 펀더멘털 분석 ({context}):

웹 검색으로:
1. 사업 모델 & 경쟁력
2. 최근 실적 (매출, 이익)
3. 재무 건전성
4. 밸류에이션 (P/E, P/B 등)
5. 성장 가능성
6. 투자 의견: Strong Buy/Buy/Hold/Sell/Strong Sell

**투자위원회용, 200단어.**
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    from portfolio_manager import PortfolioManager
    from stock_screener import ProfessionalStockScreener
    
    print("=" * 80)
    print("INVESTMENT COMMITTEE - 완전판")
    print("=" * 80)
    
    # 초기화
    pm = PortfolioManager()
    screener = ProfessionalStockScreener()
    committee = InvestmentCommittee(pm, screener)
    
    # 투자위원회 개최
    decision = committee.conduct_investment_meeting()
    
    # 결과
    print("\n" + "=" * 80)
    print("📋 CIO 최종 결정서")
    print("=" * 80)
    print(decision['cio_decision'])
    
    # 저장
    filename = f"committee_decision_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        save_data = {
            'timestamp': decision['timestamp'],
            'synced': decision['synced'],
            'cio_decision': decision['cio_decision']
        }
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 회의록 저장: {filename}")