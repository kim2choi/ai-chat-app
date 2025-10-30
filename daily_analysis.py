import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from datetime import datetime

load_dotenv()

fmp_key = os.getenv("FMP_API_KEY")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
bot_token = os.getenv("STOCK_BOT_TOKEN")
chat_id = os.getenv("STOCK_CHAT_ID")

def get_stock_data(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
    return requests.get(url).json()[0]

def daily_analysis():
    symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"📊 일일 시장 분석 ({now})\n\n"
    
    stocks_info = []
    for symbol in symbols:
        data = get_stock_data(symbol)
        change = data['changesPercentage']
        emoji = "🟢" if change > 0 else "🔴"
        report += f"{emoji} **{symbol}**: ${data['price']:.2f} ({change:+.2f}%)\n"
        stocks_info.append(f"{symbol}: ${data['price']}, 변동 {change}%")
    
    # AI 종합 분석
    prompt = f"""
당신은 포트폴리오 매니저입니다. 오늘의 주요 종목을 분석하세요.

종목 현황:
{chr(10).join(stocks_info)}

다음 형식으로 답변:

📈 시장 분위기: [한 줄 요약]

🎯 주목 종목: [가장 주목할 1-2개 종목과 이유]

💡 투자 전략: [오늘의 한 마디 조언]
"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    
    report += f"\n{response.choices[0].message.content}"
    
    return report

async def send_to_telegram(message):
    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id, 
        text=message,
        parse_mode='Markdown'
    )

if __name__ == "__main__":
    try:
        print("분석 시작...")
        report = daily_analysis()
        asyncio.run(send_to_telegram(report))
        print("✅ 분석 전송 완료")
    except Exception as e:
        print(f"❌ 에러: {e}")