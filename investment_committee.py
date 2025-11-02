import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InvestmentCommittee:
    """투자위원회 - 5개 팀 + CIO"""
    
    def __init__(self, portfolio_manager, stock_screener):
        self.pm = portfolio_manager
        self.screener = stock_screener
        self.model = "gpt-4o"
    
    def conduct_investment_meeting(self):
        """투자위원회 개최"""
        
        print("\n" + "="*80)
        print("🏛️  투자위원회 개최")
        print("="*80)
        
        # 1. 현재 포트폴리오 분석
        current = self.pm.get_current_value()
        
        print(f"\n💼 현재 포트폴리오:")
        print(f"   총 평가액: ${current['total_value']:,.2f}")
        print(f"   현금: ${current['cash']:,.2f}")
        print(f"   주식: ${current['stock_value']:,.2f}")
        print(f"   보유 종목 수: {len(current['holdings'])}개")
        
        # 2. 각 팀 분석 수행
        print("\n" + "="*80)
        print("📊 STEP 1: 각 팀별 분석")
        print("="*80)
        
        team_reports = {}
        
        # 2A. 매크로 경제 팀
        print("\n📈 STEP 1A: MACRO ECONOMIC TEAM")
        print("-"*80)
        team_reports['macro'] = self._macro_team_analysis()
        
        # 2B. 기술적 분석 팀
        print("\n📊 STEP 1B: TECHNICAL ANALYSIS TEAM")
        print("-"*80)
        team_reports['technical'] = self._technical_team_analysis(current)
        
        # 2C. 종목 발굴 팀
        print("\n🔍 STEP 1C: STOCK SCREENING TEAM")
        print("-"*80)
        team_reports['screening'] = self._screening_team_analysis(current)
        
        # 2D. 펀더멘털 분석 팀
        print("\n📈 STEP 2D: FUNDAMENTAL ANALYSIS TEAM")
        print("-"*80)
        team_reports['fundamental'] = self._fundamental_team_analysis(
            current, 
            team_reports['screening']['recommended_stocks']
        )
        
        # 3. CIO 최종 결정
        print("\n👔 STEP 3: CIO 최종 의사결정")
        print("="*80)
        cio_decision = self._cio_final_decision(current, team_reports)
        
        # 4. 회의록 저장
        meeting_record = {
            'timestamp': datetime.now().isoformat(),
            'current_portfolio': current,
            'team_reports': team_reports,
            'cio_decision': cio_decision
        }
        
        self._save_meeting_record(meeting_record)
        
        return meeting_record
    
    def _macro_team_analysis(self):
        """매크로 경제 팀 분석"""
        
        print("   💼 Team Lead: Sarah Johnson")
        print("   📋 글로벌 경제 및 시장 동향 분석")
        
        prompt = """
당신은 투자위원회의 매크로 경제 분석 팀장입니다.

현재 글로벌 경제 상황을 분석하고 투자 방향을 제시하세요:

1. 주요 경제 지표 (금리, 인플레이션, GDP)
2. 지정학적 리스크
3. 섹터별 전망
4. 투자 추천 방향

간결하게 핵심만 작성하세요 (500자 이내).
"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        print(f"\n{analysis}\n")
        
        return {
            'team': 'Macro Economic',
            'lead': 'Sarah Johnson',
            'analysis': analysis
        }
    
    def _technical_team_analysis(self, current):
        """기술적 분석 팀"""
        
        print("   💼 Team Lead: Michael Chen")
        print("   📋 포트폴리오 기술적 분석")
        
        holdings_summary = []
        for h in current['holdings']:
            holdings_summary.append(f"- {h['symbol']}: {h['shares']}주, ${h['current_value']:.2f}")
        
        prompt = f"""
당신은 기술적 분석 전문가입니다.

현재 포트폴리오:
{''.join(holdings_summary) if holdings_summary else '보유 종목 없음'}

각 보유 종목의 기술적 분석 및 추천 액션을 제시하세요:
- 보유유지 (Hold)
- 일부매도 (Partial Sell)
- 전량매도 (Full Sell)
- 추가매수 (Add)

간결하게 작성하세요 (500자 이내).
"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        print(f"\n{analysis}\n")
        
        return {
            'team': 'Technical Analysis',
            'lead': 'Michael Chen',
            'analysis': analysis
        }
    
    def _screening_team_analysis(self, current):
        """종목 발굴 팀"""
        
        print("   💼 Team Lead: Jennifer Lee")
        print("   📋 신규 종목 발굴")
        
        # 종목 스크리닝
        print("\n   🔍 종목 스크리닝 실행 중...")
        candidates = self.screener.screen_stocks(max_results=4)
        
        recommended = []
        for stock in candidates:
            recommended.append(stock['symbol'])
            print(f"      - {stock['symbol']} 완료")
        
        print(f"\n✅ {len(recommended)} 종목 선정 완료")
        
        return {
            'team': 'Stock Screening',
            'lead': 'Jennifer Lee',
            'recommended_stocks': recommended,
            'full_data': candidates
        }
    
    def _fundamental_team_analysis(self, current, recommended_stocks):
        """펀더멘털 분석 팀"""
        
        print("   💼 Team Lead: Emily Watson")
        print("   📋 펀더멘털 분석")
        
        print("\n   보유 종목 분석 중...")
        print("   발굴 종목 분석 중...")
        
        for symbol in recommended_stocks:
            print(f"      - {symbol} 완료")
        
        prompt = f"""
당신은 펀더멘털 분석 전문가입니다.

신규 추천 종목: {', '.join(recommended_stocks)}

각 종목에 대해 간략한 투자 의견을 작성하세요:
- 투자 매력도
- 주요 리스크
- 적정 투자 비중

간결하게 작성하세요 (500자 이내).
"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        return {
            'team': 'Fundamental Analysis',
            'lead': 'Emily Watson',
            'analysis': analysis,
            'analyzed_stocks': recommended_stocks
        }
    
    def _cio_final_decision(self, current, team_reports):
        """CIO 최종 의사결정"""
        
        print("\n🤖 CIO 최종 통합 분석 중...")
        print("="*80)
        
        # 추천 종목 리스트
        recommended = team_reports['screening']['recommended_stocks']
        print(f"   ✅ {len(recommended)}개 종목 발굴 완료")
        
        # 현재 보유 종목
        holdings_detail = []
        for h in current['holdings']:
            holdings_detail.append(
                f"- {h['symbol']}: {h['shares']}주, "
                f"평가액 ${h['current_value']:.2f}, "
                f"수익률 {h['profit_pct']:+.1f}%"
            )
        
        # 제약 조건 명확히 설정
        max_investment = current['cash'] * 0.9  # 현금의 90%만 사용
        
        prompt = f"""
당신은 투자위원회의 최고투자책임자(CIO)입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  절대적 제약 조건 (반드시 준수)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 현재 포트폴리오:
- 총 평가액: ${current['total_value']:,.2f}
- 사용 가능 현금: ${current['cash']:,.2f}
- 주식 평가액: ${current['stock_value']:,.2f}
- 보유 종목 수: {len(current['holdings'])}개

💵 투자 제약:
- 최대 투자 가능 금액: ${max_investment:,.2f}
- 이 금액을 절대 초과할 수 없습니다
- 현금 10%는 비상금으로 보유

📊 현재 보유 종목:
{chr(10).join(holdings_detail) if holdings_detail else "없음"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 각 팀 분석 결과:

1. 매크로 팀 ({team_reports['macro']['lead']}):
{team_reports['macro']['analysis']}

2. 기술적 분석 팀 ({team_reports['technical']['lead']}):
{team_reports['technical']['analysis']}

3. 펀더멘털 팀 ({team_reports['fundamental']['lead']}):
{team_reports['fundamental']['analysis']}

4. 발굴 종목: {', '.join(recommended)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 작성 지침:

1. 보유 종목별 결정:
   - 각 보유 종목에 대해 "보유유지" 또는 "일부매도(X%)" 또는 "전량매도" 결정
   - 매도 금액을 명시할 것

2. 신규 매수 결정:
   - 발굴 종목 중 매수할 종목 선정
   - **중요**: 각 종목별 매수 금액을 명시 (예: $500, $1000)
   - **모든 매수 금액의 합계는 ${max_investment:,.2f}를 절대 초과 불가**
   - 만약 현금이 부족하면 매수 금액을 줄이거나 종목 수를 줄일 것

3. 금액 계산 예시:
   - 현금 $1000이면 → 최대 $900 투자 가능
   - 3개 종목 매수 시 → 각각 $300씩
   - 2개 종목 매수 시 → 각각 $450씩

출력 형식:
## CIO 최종 결정서

### 1. Executive Summary
- 핵심 투자 방향
- 예상 효과

### 2. 보유 종목별 결정
- 종목명: 결정 (보유유지/일부매도/전량매도)
- 근거: 
- 실행 타이밍:

### 3. 신규 매수 결정
- 종목명: 매수
  - 근거:
  - 금액: $XXX (구체적 금액 필수)
  - 비중: XX%

(다음 종목도 동일 형식)

**매수 금액 합계: $XXX (최대 ${max_investment:,.2f} 이내)**

### 4. 리밸런싱 후 포트폴리오
- 각 종목 비중
- 섹터 분산
- 예상 리스크 점수

### 5. 실행 계획
1단계: 즉시 - 어떤 주문
2단계: X일내 - 어떤 작업
3단계: 모니터링 - 어떤 지표

### 6. 리스크 관리
- 주요 리스크
- 대응 방안
- 손절 기준
"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        decision = response.choices[0].message.content
        
        return decision
    
    def _save_meeting_record(self, record):
        """회의록 저장"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_record_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 회의록 저장: {filename}")


# ═══════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    from portfolio_manager import PortfolioManager
    from stock_screener import ProfessionalStockScreener
    
    pm = PortfolioManager()
    screener = ProfessionalStockScreener()
    
    committee = InvestmentCommittee(pm, screener)
    
    print("투자위원회 테스트")
    print("=" * 80)
    
    result = committee.conduct_investment_meeting()
    
    print("\n✅ 투자위원회 완료")
    print(f"CIO 결정:\n{result['cio_decision'][:500]}...")