import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

fmp_key = os.getenv("FMP_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_stock_data(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
    return requests.get(url).json()[0]

def analyze_portfolio(stocks_data):
    """여러 종목을 한 번에 분석"""
    summary = "다음 종목들을 분석:\n\n"
    
    for stock in stocks_data:
        summary += f"- {stock['symbol']}: ${stock['price']} "
        summary += f"(변동: {stock['changesPercentage']}%, P/E: {stock['pe']})\n"
    
    prompt = f"""
당신은 포트폴리오 매니저입니다.

{summary}

각 종목에 대해:
1. 매수/보유/매도 추천
2. 포트폴리오 비중 (총 100%)
3. 한 줄 이유

간결하게 표 형식으로.
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    
    return response.choices[0].message.content

# 테스트
symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"]

print("=== 포트폴리오 분석 중... ===\n")

stocks = []
for symbol in symbols:
    data = get_stock_data(symbol)
    stocks.append(data)
    print(f"✓ {symbol}: ${data['price']}")

print("\n=== AI 포트폴리오 추천 ===\n")
recommendation = analyze_portfolio(stocks)
print(recommendation)

# 결과 저장
with open("portfolio_recommendation.json", "w") as f:
    json.dump({
        "stocks": stocks,
        "recommendation": recommendation
    }, f, indent=2)

print("\n결과 저장: portfolio_recommendation.json")
