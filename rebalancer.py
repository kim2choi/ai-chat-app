import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PortfolioRebalancer:
    """
    AI 기반 포트폴리오 리밸런싱
    - 현재 보유 vs 스크리너 발굴 비교
    - 매수/매도 제안
    - 구체적 실행 계획
    """
    
    def __init__(self, portfolio_manager, stock_screener):
        self.pm = portfolio_manager
        self.screener = stock_screener
    
    def generate_rebalancing_plan(self, target_allocation=None):
        """리밸런싱 계획 생성"""
        
        print("=" * 70)
        print("🔄 AI 리밸런싱 분석 시작")
        print("=" * 70)
        
        # 1. 현재 포트폴리오 상태
        current = self.pm.get_current_value()
        
        # 2. 시장 스캔 (새로운 기회)
        print("\n🔍 시장 스캔 중...")
        discovered = self.screener.scan_all_strategies(stocks_per_strategy=2)
        
        # 3. AI 리밸런싱 분석
        print("\n🤖 AI 리밸런싱 계획 수립 중...\n")
        plan = self._ai_rebalancing_decision(current, discovered)
        
        return plan
    
    def _ai_rebalancing_decision(self, current_portfolio, discovered_stocks):
        """AI 리밸런싱 의사결정"""
        
        # 현재 포트폴리오 요약
        current_summary = f"""
## 현재 포트폴리오
총 평가액: ${current_portfolio['total_value']:,.2f}
현금: ${current_portfolio['cash']:,.2f}
주식: ${current_portfolio['stock_value']:,.2f}

### 보유 종목 ({len(current_portfolio['holdings'])}개)
"""
        
        for holding in current_portfolio['holdings']:
            current_summary += f"""
- {holding['symbol']}: {holding['shares']}주
  현재가: ${holding['current_price']:.2f}
  평가액: ${holding['current_value']:.2f}
  수익: ${holding['profit']:.2f} ({holding['profit_pct']:+.2f}%)
"""
        
        # 발굴된 종목 요약
        discovered_summary = "\n## 스크리너 발굴 종목\n\n"
        
        for strategy_key, data in discovered_stocks['strategies'].items():
            config = data['config']
            picks = data['picks']
            
            discovered_summary += f"\n### {config['name']}\n"
            for pick in picks[:2]:  # 각 전략당 상위 2개
                discovered_summary += f"- {pick['symbol']}: ${pick['price']:.2f} (점수: {pick['score']}/100)\n"
        
        # CIO 리포트
        discovered_summary += f"\n### CIO 분석\n{discovered_stocks['cio_report'][:500]}...\n"
        
        # AI 리밸런싱 프롬프트
        prompt = f"""
당신은 30년 경력의 포트폴리오 매니저입니다.

{current_summary}

{discovered_summary}

**리밸런싱 제안서 작성:**

1. Executive Summary
   - 현재 포트폴리오 평가 (한 줄)
   - 핵심 제안 (한 줄)

2. 매도 제안
   - 매도할 종목과 이유
   - 각 종목별: 전량/일부, 예상 회수 금액
   - 없으면 "매도 제안 없음"

3. 매수 제안
   - 매수할 신규 종목 (발굴 종목에서)
   - 각 종목별: 추천 금액, 예상 주수, 이유
   - 최대 3개까지

4. 리밸런싱 후 예상 포트폴리오
   - 종목별 비중 (%)
   - 예상 섹터 분산
   - 예상 리스크 점수 (0-100)

5. 실행 우선순위
   1단계: [먼저 할 것]
   2단계: [다음 할 것]

6. 리스크 및 주의사항

**조건:**
- 현금이 없으면 매수 불가
- 매도 후 현금으로 매수 가능
- 실행 가능한 구체적 계획
- 보수적 접근 (급격한 변화 자제)

간결하고 실행 가능하게 작성하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'current_portfolio': current_portfolio,
            'discovered_stocks': discovered_stocks,
            'rebalancing_plan': response.choices[0].message.content
        }
    
    def format_for_telegram(self, plan):
        """텔레그램용 포맷"""
        
        message = f"""
🔄 **리밸런싱 제안**
⏰ {plan['timestamp']}

💼 **현재 상태**
평가액: ${plan['current_portfolio']['total_value']:,.2f}
현금: ${plan['current_portfolio']['cash']:,.2f}

━━━━━━━━━━━━━━━━━━━━

{plan['rebalancing_plan']}

━━━━━━━━━━━━━━━━━━━━

💡 이 제안을 실행하시겠습니까?
"""
        
        return message


# 테스트
if __name__ == "__main__":
    from portfolio_manager import PortfolioManager
    from stock_screener import ProfessionalStockScreener
    from kis_connector import KISConnector
    
    print("=" * 70)
    print("포트폴리오 리밸런싱 시스템 테스트")
    print("=" * 70)
    
    # 1. 실제 포트폴리오 로드
    print("\n1. 실제 포트폴리오 동기화...")
    pm = PortfolioManager()
    kis = KISConnector()
    
    try:
        real_portfolio = kis.sync_to_portfolio_manager(pm)
        print(f"✅ 포트폴리오 동기화 완료: {len(real_portfolio['holdings'])}개 종목")
    except Exception as e:
        print(f"⚠️  동기화 실패: {e}")
        print("   테스트 데이터로 진행...")
    
    # 2. 스크리너 초기화
    print("\n2. 스크리너 초기화...")
    screener = ProfessionalStockScreener()
    
    # 3. 리밸런서 초기화
    print("\n3. 리밸런서 초기화...")
    rebalancer = PortfolioRebalancer(pm, screener)
    
    # 4. 리밸런싱 계획 생성
    print("\n4. 리밸런싱 계획 생성...\n")
    plan = rebalancer.generate_rebalancing_plan()
    
    # 5. 결과 출력
    print("\n" + "=" * 70)
    print("📊 리밸런싱 제안서")
    print("=" * 70)
    print(plan['rebalancing_plan'])
    
    # 6. 저장
    filename = f"rebalancing_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        # JSON 직렬화 가능하도록 변환
        save_plan = {
            'timestamp': plan['timestamp'],
            'rebalancing_plan': plan['rebalancing_plan']
        }
        json.dump(save_plan, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 계획 저장: {filename}")