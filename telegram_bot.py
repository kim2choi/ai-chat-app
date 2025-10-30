import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# API 설정
fmp_key = os.getenv("FMP_API_KEY")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

def get_stock_data(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
    response = requests.get(url)
    return response.json()[0]

def analyze_stock(stock_data):
    prompt = f"""
당신은 전문 주식 애널리스트입니다.

종목: {stock_data['name']} ({stock_data['symbol']})
현재가: ${stock_data['price']}
변동: {stock_data['changesPercentage']}%
P/E: {stock_data['pe']}

3줄 분석:
1. 현재 상태
2. 강점/약점  
3. 투자 의견
"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    
    return response.choices[0].message.content

# 봇 명령어
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! AI 투자 분석 봇입니다.\n\n"
        "사용법:\n"
        "/analyze AAPL - 애플 분석\n"
        "/portfolio - 5개 종목 포트폴리오"
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("종목 코드를 입력하세요. 예: /analyze AAPL")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"{symbol} 분석 중... ⏳")
    
    try:
        data = get_stock_data(symbol)
        analysis = analyze_stock(data)
        
        message = f"""
📊 {data['name']} ({symbol})
💰 가격: ${data['price']}
📈 변동: {data['changesPercentage']}%

🤖 AI 분석:
{analysis}
"""
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"오류: {str(e)}")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("포트폴리오 분석 중... ⏳")
    
    symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"]
    stocks_info = []
    
    for symbol in symbols:
        data = get_stock_data(symbol)
        stocks_info.append(f"{symbol}: ${data['price']}")
    
    message = "📊 주요 종목 현황:\n\n" + "\n".join(stocks_info)
    await update.message.reply_text(message)

def main():
    app = Application.builder().token(bot_token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("portfolio", portfolio))
    
    print("봇 시작됨! Ctrl+C로 종료")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()