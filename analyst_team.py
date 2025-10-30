import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

fmp_key = os.getenv("FMP_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AnalystTeam:
    def __init__(self):
        self.analysts = {
            "financial": FinancialAnalyst(),
            "sentiment": SentimentAnalyst(),
            "cio": CIO()
        }
    
    def analyze_stock(self, symbol):
        """종목 종합 분석"""
        # 데이터 수집
        stock_data = self.get_stock_data(symbol)
        
        # 각 애널리스트 분석 (CIO 제외)
        reports = {}
        for name, analyst in self.analysts.items():
            if name != "cio":
                reports[name] = analyst.analyze(stock_data)
        
        # CIO 최종 판단
        final_decision = self.analysts["cio"].decide(stock_data, reports)
        
        return final_decision
    
    def get_stock_data(self, symbol):
        """FMP에서 데이터 가져오기"""
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
        quote = requests.get(quote_url).json()[0]
        return quote


class FinancialAnalyst:
    """재무 애널리스트 - 숫자 깊이 분석"""
    
    def analyze(self, data):
        prompt = f"""
당신은 20년 경력의 재무 애널리스트입니다.

종목: {data['name']} ({data['symbol']})
현재가: ${data['price']}
시가총액: ${data['marketCap']:,}
P/E 비율: {data.get('pe', 'N/A')}
EPS: ${data.get('eps', 'N/A')}
52주 최고/최저: ${data['yearHigh']} / ${data['yearLow']}

**전문적인 재무 분석을 제공하세요:**

1. 밸류에이션 평가
   - P/E 비율 적정성
   - 동종 업계 대비 평가
   - 현재 주가 위치 (52주 기준)

2. 재무 건전성
   - 시가총액 규모
   - 수익성 지표

3. 투자 의견
   - 재무적 관점 매수/보유/매도
   - 목표가 제시 (간단한 근거)

간결하게 핵심만 작성하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        return {
            "analyst": "재무 애널리스트",
            "analysis": response.choices[0].message.content
        }


class SentimentAnalyst:
    """시장 심리 애널리스트 - 뉴스 감성"""
    
    def analyze(self, data):
        change = data['changesPercentage']
        
        prompt = f"""
당신은 시장 심리 전문 애널리스트입니다.

종목: {data['name']} ({data['symbol']})
오늘 변동: {change:+.2f}%
거래량: {data.get('volume', 'N/A')}

**시장 심리 분석:**

1. 현재 시장 센티먼트
   - 투자자 심리 (공포/탐욕)
   - 모멘텀 평가

2. 리스크 요인
   - 단기 변동성
   - 주의할 점

3. 심리적 관점 의견
   - 매수/보유/매도
   - 타이밍 조언

간결하게 작성하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        
        return {
            "analyst": "시장 심리 애널리스트",
            "analysis": response.choices[0].message.content
        }


class CIO:
    """최고투자책임자 - 최종 의사결정"""
    
    def decide(self, data, reports):
        # 모든 애널리스트 의견 통합
        all_analysis = "\n\n".join([
            f"## {report['analyst']}\n{report['analysis']}"
            for report in reports.values()
        ])
        
        prompt = f"""
당신은 CIO(최고투자책임자)입니다. 애널리스트들의 보고를 받고 최종 결정을 내립니다.

종목: {data['name']} ({data['symbol']})
현재가: ${data['price']}

## 애널리스트 보고서
{all_analysis}

**최종 투자 의견:**

1. 종합 평가
   - 모든 분석 종합
   - 핵심 인사이트

2. 최종 결정
   - 명확한 매수/보유/매도
   - 투자 비중 제안 (%)
   - 목표가 (있다면)

3. 리스크 및 주의사항

4. 액션 플랜
   - 구체적인 다음 단계

전문적이고 확신있게 작성하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        return {
            "symbol": data['symbol'],
            "company": data['name'],
            "price": data['price'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "analyst_reports": reports,
            "cio_decision": response.choices[0].message.content
        }


# 테스트
if __name__ == "__main__":
    team = AnalystTeam()
    
    symbol = "AAPL"
    print(f"=== {symbol} 전문가팀 분석 시작 ===\n")
    
    result = team.analyze_stock(symbol)
    
    print(f"종목: {result['company']} ({result['symbol']})")
    print(f"현재가: ${result['price']}")
    print(f"분석 시각: {result['timestamp']}\n")
    
    print("=" * 60)
    print("애널리스트 보고서")
    print("=" * 60)
    for name, report in result['analyst_reports'].items():
        print(f"\n## {report['analyst']}")
        print(report['analysis'])
    
    print("\n" + "=" * 60)
    print("CIO 최종 결정")
    print("=" * 60)
    print(result['cio_decision'])