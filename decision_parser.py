from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DecisionParser:
    """CIO 결정서를 실행 가능한 주문으로 파싱"""
    
    def parse_decision(self, cio_decision: str, portfolio: Dict) -> Dict:
        """
        CIO 결정서를 파싱하여 구체적인 주문 생성
        
        Returns:
            {
                'sells': [{'symbol': 'ROL', 'quantity': 0.5, 'reason': '...'}],
                'buys': [{'symbol': 'FSLR', 'amount': 3700, 'reason': '...'}]
            }
        """
        
        prompt = f"""
당신은 투자 결정서를 파싱하는 전문가입니다.

# CIO 결정서
{cio_decision}

# 현재 포트폴리오
총 평가액: ${portfolio['total_value']:.2f}
현금: ${portfolio['cash']:.2f}

보유 종목:
{self._format_holdings(portfolio['holdings'])}

# 작업
CIO 결정서에서 **구체적인 매도/매수 지시**를 추출하세요.

출력 형식 (JSON만, 마크다운 없이):
{{
    "sells": [
        {{
            "symbol": "ROL",
            "action": "50% 매도",
            "quantity": 0.5,
            "reason": "집중도 해소"
        }}
    ],
    "buys": [
        {{
            "symbol": "FSLR",
            "target_amount": 3700,
            "reason": "태양광 성장"
        }}
    ],
    "summary": "ROL 일부매도, FSLR 매수"
}}

**규칙:**
1. "보유유지"는 제외
2. 매도는 정확한 주수 계산
3. 매수는 목표 금액
4. 없으면 빈 배열 []

**중요:** JSON 형식만 출력하세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # 디버깅
        print("GPT 응답:")
        print(content)
        print("-" * 80)
        
        # 마크다운 제거 (혹시 모르니)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        
        return result
    
    def _format_holdings(self, holdings):
        """보유 종목 포맷"""
        if not holdings:
            return "없음"
        
        lines = []
        for h in holdings:
            lines.append(f"- {h['symbol']}: {h['shares']:.4f}주 (${h['current_value']:.2f})")
        return "\n".join(lines)
    
    def calculate_buy_quantities(self, buys: List[Dict], current_prices: Dict) -> List[Dict]:
        """
        매수 금액을 주수로 변환
        
        Args:
            buys: [{'symbol': 'FSLR', 'target_amount': 3700}]
            current_prices: {'FSLR': 250.5}
        
        Returns:
            [{'symbol': 'FSLR', 'quantity': 14, 'price': 250.5}]
        """
        
        result = []
        
        for buy in buys:
            symbol = buy['symbol']
            amount = buy['target_amount']
            price = current_prices.get(symbol)
            
            if not price:
                continue
            
            # 주수 계산 (소수점 버림)
            quantity = int(amount / price)
            
            if quantity > 0:
                result.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total_cost': quantity * price,
                    'reason': buy.get('reason', '')
                })
        
        return result


# ═══════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = DecisionParser()
    
    # 테스트 결정서
    test_decision = """
    ## 보유 종목별 결정
    - ROL: 일부매도(50%)
    - LOMA: 보유유지
    
    ## 신규 매수
    - FSLR: 매수, 금액 $3700
    """
    
    test_portfolio = {
        'total_value': 10000,
        'cash': 5000,
        'holdings': [
            {'symbol': 'ROL', 'shares': 1.0, 'current_value': 3000},
            {'symbol': 'LOMA', 'shares': 1.0, 'current_value': 2000}
        ]
    }
    
    result = parser.parse_decision(test_decision, test_portfolio)
    print("\n파싱 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))