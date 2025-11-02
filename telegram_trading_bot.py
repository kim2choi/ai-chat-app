import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from portfolio_manager import PortfolioManager
from kis_connector import KISConnector
from stock_screener import ProfessionalStockScreener
from investment_committee import InvestmentCommittee
from order_executor import OrderExecutor
from decision_parser import DecisionParser

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
executor = OrderExecutor()
parser = DecisionParser()

# 전역 변수: 최근 결정 저장
last_decision = None
pending_orders = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 메시지"""
    message = """
🏦 **AI Investment Committee**

**명령어:**
/portfolio - 포트폴리오 조회
/sync - 계좌 동기화
/rebalance - 투자위원회 소집
/approve - CIO 결정 승인 및 실행
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
        pm.save()

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
        
        # 전역 변수에 저장!
        global last_decision
        last_decision = decision
        
        # 결과 요약
        summary = f"""
🏛️  **투자위원회 결정**
⏰ {decision['timestamp']}

━━━━━━━━━━━━━━━━━━━━

{decision['cio_decision'][:1500]}

━━━━━━━━━━━━━━━━━━━━

💾 전체 회의록이 저장되었습니다.

💡 **실행하려면:** `/approve`
"""
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}\n\n자세한 내용은 로그를 확인하세요.")
        logging.error(f"Rebalance error: {e}", exc_info=True)


async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CIO 결정 승인 및 실행 준비"""
    
    global last_decision, pending_orders
    
    # 결정 확인
    if not last_decision:
        await update.message.reply_text(
            "❌ 실행할 결정이 없습니다.\n"
            "먼저 /rebalance를 실행하세요."
        )
        return
    
    await update.message.reply_text("🔍 결정 분석 중...")
    
    try:
        # 1. 결정 파싱
        current = pm.get_current_value()
        
        parsed = parser.parse_decision(
            last_decision['cio_decision'],
            current
        )
        
        # 2. 매수 종목 가격 조회
        await update.message.reply_text("📊 현재 가격 조회 중...")
        
        current_prices = {}
        for buy in parsed['buys']:
            symbol = buy['symbol']
            price = kis.get_current_price(symbol)
            if price:
                current_prices[symbol] = price
        
        # 3. 매수 주수 계산
        buy_orders = parser.calculate_buy_quantities(parsed['buys'], current_prices)
        
        # 4. 주문 목록 생성
        pending_orders = {
            'sells': parsed['sells'],
            'buys': buy_orders,
            'summary': parsed['summary']
        }
        
        # 5. 확인 메시지
        msg = f"""
📋 **실행 계획**

{parsed['summary']}

━━━━━━━━━━━━━━━━━━━━

"""
        
        # 매도 목록
        if pending_orders['sells']:
            msg += "**매도:**\n"
            for sell in pending_orders['sells']:
                msg += f"• {sell['symbol']}: {sell['quantity']:.4f}주\n"
                msg += f"  이유: {sell['reason']}\n"
            msg += "\n"
        
        # 매수 목록
        if pending_orders['buys']:
            msg += "**매수:**\n"
            for buy in pending_orders['buys']:
                msg += f"• {buy['symbol']}: {buy['quantity']}주 @ ${buy['price']:.2f}\n"
                msg += f"  총액: ${buy['total_cost']:.2f}\n"
                msg += f"  이유: {buy.get('reason', 'N/A')}\n"
            msg += "\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "⚠️  **최종 확인**\n\n"
        msg += "실행하시려면:\n"
        msg += "`/confirm_all`"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}")
        logging.error(f"Approve error: {e}", exc_info=True)


async def confirm_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모든 주문 일괄 실행"""
    
    global pending_orders
    
    if not pending_orders:
        await update.message.reply_text(
            "❌ 실행할 주문이 없습니다.\n"
            "먼저 /approve를 실행하세요."
        )
        return
    
    await update.message.reply_text("🚀 주문 실행 중...\n잠시만 기다려주세요.")
    
    results = {
        'sells': [],
        'buys': [],
        'errors': []
    }
    
    try:
        # 1. 매도 실행
        for sell in pending_orders['sells']:
            await update.message.reply_text(f"📤 {sell['symbol']} 매도 중...")
            
            result = executor.execute_sell(
                symbol=sell['symbol'],
                quantity=int(sell['quantity'])
            )
            
            if result['success']:
                results['sells'].append({
                    'symbol': sell['symbol'],
                    'quantity': sell['quantity'],
                    'price': result.get('executed_price', 0)
                })
                await update.message.reply_text(f"✅ {sell['symbol']} 매도 완료!")
            else:
                results['errors'].append(f"{sell['symbol']} 매도 실패: {result.get('error')}")
                await update.message.reply_text(f"❌ {sell['symbol']} 매도 실패")
        
        # 2. 매수 실행
        for buy in pending_orders['buys']:
            await update.message.reply_text(f"📤 {buy['symbol']} 매수 중...")
            
            result = executor.execute_buy(
                symbol=buy['symbol'],
                quantity=buy['quantity']
            )
            
            if result['success']:
                results['buys'].append({
                    'symbol': buy['symbol'],
                    'quantity': buy['quantity'],
                    'price': result.get('executed_price', 0)
                })
                await update.message.reply_text(f"✅ {buy['symbol']} 매수 완료!")
            else:
                results['errors'].append(f"{buy['symbol']} 매수 실패: {result.get('error')}")
                await update.message.reply_text(f"❌ {buy['symbol']} 매수 실패")
        
        # 3. 최종 리포트
        report = "🎉 **실행 완료!**\n\n"
        
        if results['sells']:
            report += "**매도:**\n"
            for s in results['sells']:
                report += f"✅ {s['symbol']}: {s['quantity']:.4f}주\n"
            report += "\n"
        
        if results['buys']:
            report += "**매수:**\n"
            for b in results['buys']:
                report += f"✅ {b['symbol']}: {b['quantity']}주\n"
            report += "\n"
        
        if results['errors']:
            report += "**오류:**\n"
            for err in results['errors']:
                report += f"❌ {err}\n"
        
        report += "\n🔄 포트폴리오 동기화 중..."
        
        await update.message.reply_text(report, parse_mode='Markdown')
        
        # 4. 동기화
        kis.sync_to_portfolio_manager(pm)
        await update.message.reply_text("✅ 모든 작업 완료!")
        
        # 5. 초기화
        pending_orders = None
        
    except Exception as e:
        await update.message.reply_text(f"❌ 심각한 오류: {e}")
        logging.error(f"Confirm all error: {e}", exc_info=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말"""
    message = """
🏦 AI Investment Committee

명령어:
/portfolio - 포트폴리오 조회
/sync - 계좌 동기화
/rebalance - 투자위원회 소집
/approve - CIO 결정 승인
/confirm_all - 주문 실행
/help - 도움말
"""
    await update.message.reply_text(message)  # parse_mode 제거!


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
    application.add_handler(CommandHandler("approve", approve_cmd))
    application.add_handler(CommandHandler("confirm_all", confirm_all_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    
    print("🤖 텔레그램 투자위원회 봇 시작...")
    print("Ctrl+C로 종료")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
