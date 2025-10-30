import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# API 설정
fmp_key = os.getenv("FMP_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_stock_data(symbol):
    """FMP에서 주식 데이터 가져오기"""
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
    response = requests.get(url)
    return response.json()[0]

def analyze_stock(stock_data):
    """GPT-4o-mini로 주식 분석"""
    prompt = f"""
당신은 전문 주식 애널리스트입니다.

다음 데이터를 분석하세요:
- 종목: {stock_data['name']} ({stock_data['symbol']})
- 현재가: ${stock_data['price']}
- 일일 변동: {stock_data['changesPercentage']}%
- 52주 최고: ${stock_data['yearHigh']}
- 52주 최저: ${stock_data['yearLow']}
- P/E 비율: {stock_data['pe']}
- 시가총액: ${stock_data['marketCap']:,}

간결하게 3줄로 분석:
1. 현재 상태
2. 강점/약점
3. 투자 의견 (매수/보유/매도)
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    
    return response.choices[0].message.content

# 테스트
symbol = "AAPL"
print(f"=== {symbol} 분석 중... ===\n")

data = get_stock_data(symbol)
analysis = analyze_stock(data)

print(f"회사: {data['name']}")
print(f"가격: ${data['price']}\n")
print("AI 분석:")
print(analysis)