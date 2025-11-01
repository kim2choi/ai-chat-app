import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from portfolio_manager import PortfolioManager
from kis_connector import KISConnector
from stock_screener import ProfessionalStockScreener
from investment_committee import InvestmentCommittee

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 초기화
pm = PortfolioManager()
kis = KISConnector()
screener = ProfessionalStockScreener()
committee = InvestmentCommittee(pm, screener)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 메시지"""
    message = """
🏦 **AI Investment Committee**

**명령어:**
/portfolio - 포트폴리오 조회
/sync - 계좌 동기화
/rebalance - 투자위원회 소집
/help - 도움말
"""
    await update.message.reply_text(message, parse_mode='Markdown')

async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """포트폴리오 조회"""
    await update.message.reply_text("📊 포트폴리오 조회 중...")
    
    try:
        current = pm.get_current_value()
        
        msg = f"""
💼 **포트폴리오**

📊 총 평가액: ${current['total_value']:,.2f}
💵 현금: ${current['cash']:,.2f}
📈 주식: ${current['stock_value']:,.2f}
🔢 종목 수: {len(current['holdings'])}개

**보유 종목:**
"""
        
        for holding in current['holdings']:
            profit_emoji = "🟢" if holding['profit'] > 0 else "🔴" if holding['profit'] < 0 else "⚪"
            msg += f"\n{profit_emoji} {holding['symbol']}: {holding['shares']:.4f}주"
            msg += f"\n   ${holding['current_value']:.2f} ({holding['profit_pct']:+.2f}%)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}")

async def sync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """한투 계좌 동기화"""
    await update.message.reply_text("🔄 계좌 동기화 중...")
    
    try:
        portfolio = kis.sync_to_portfolio_manager(pm)
        
        msg = f"""
✅ **동기화 완료**

📊 총 평가액: ${portfolio['total_value']:,.2f}
📈 보유 종목: {len(portfolio['holdings'])}개

"""
        
        for symbol, data in portfolio['holdings'].items():
            msg += f"• {symbol}: {data['shares']:.4f}주 (${data['current_value']:.2f})\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}")

async def rebalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """투자위원회 리밸런싱"""
    await update.message.reply_text(
        "🏛️  **투자위원회 소집**\n\n"
        "5개 팀이 분석 중입니다...\n"
        "약 15-20분 소요됩니다."
    )
    
    try:
        # 투자위원회 개최
        decision = committee.conduct_investment_meeting()
        
        # 결과 요약
        summary = f"""
🏛️  **투자위원회 결정**
⏰ {decision['timestamp']}

━━━━━━━━━━━━━━━━━━━━

{decision['cio_decision'][:1500]}

━━━━━━━━━━━━━━━━━━━━

💾 전체 회의록이 저장되었습니다.
"""
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}\n\n자세한 내용은 로그를 확인하세요.")
        logging.error(f"Rebalance error: {e}", exc_info=True)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말"""
    message = """
🏦 **AI Investment Committee**

📊 **/portfolio**
현재 포트폴리오 조회

🔄 **/sync**
한투 계좌 실시간 동기화

🏛️  **/rebalance**
투자위원회 소집 (15-20분)
- Market Intelligence Team
- Risk Management Team
- Technical Analysis Team
- Fundamental Analysis Team
- CIO 최종 결정

💡 **/help**
도움말
"""
    await update.message.reply_text(message, parse_mode='Markdown')

def main():
    """메인 실행"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN이 .env에 없습니다!")
        return
    
    application = Application.builder().token(token).build()
    
    # 명령어 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("portfolio", portfolio_cmd))
    application.add_handler(CommandHandler("sync", sync_cmd))
    application.add_handler(CommandHandler("rebalance", rebalance_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    
    print("🤖 텔레그램 투자위원회 봇 시작...")
    print("Ctrl+C로 종료")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()