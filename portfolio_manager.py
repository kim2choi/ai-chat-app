import os
import json
from datetime import datetime
from typing import Dict, List
import requests
from dotenv import load_dotenv

load_dotenv()

fmp_key = os.getenv("FMP_API_KEY")

class PortfolioManager:
    """
    전문가급 포트폴리오 관리 시스템
    - 보유 종목 추적
    - 실시간 수익률 계산
    - 포트폴리오 분석
    """
    
    def __init__(self, portfolio_file='portfolio.json'):
        self.portfolio_file = portfolio_file
        self.portfolio = self._load_portfolio()
    
    def _load_portfolio(self) -> Dict:
        """포트폴리오 로드"""
        try:
            with open(self.portfolio_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # 초기 포트폴리오
            return {
                'cash': 100000,  # $100k 현금
                'holdings': {},   # 보유 종목
                'transactions': [],  # 거래 내역
                'created_at': datetime.now().isoformat()
            }
    
    def _save_portfolio(self):
        """포트폴리오 저장"""
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=2)
    
    def add_position(self, symbol: str, shares: int, price: float, date: str = None):
        """포지션 추가 (매수)"""
        
        if date is None:
            date = datetime.now().isoformat()
        
        cost = shares * price
        
        # 현금 확인
        if cost > self.portfolio['cash']:
            return {
                'success': False,
                'message': f'현금 부족: ${self.portfolio["cash"]:.2f} < ${cost:.2f}'
            }
        
        # 보유 종목 업데이트
        if symbol in self.portfolio['holdings']:
            holding = self.portfolio['holdings'][symbol]
            total_shares = holding['shares'] + shares
            total_cost = holding['total_cost'] + cost
            holding['shares'] = total_shares
            holding['avg_price'] = total_cost / total_shares
            holding['total_cost'] = total_cost
        else:
            self.portfolio['holdings'][symbol] = {
                'shares': shares,
                'avg_price': price,
                'total_cost': cost,
                'first_purchase': date
            }
        
        # 현금 차감
        self.portfolio['cash'] -= cost
        
        # 거래 기록
        self.portfolio['transactions'].append({
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'cost': cost,
            'date': date
        })
        
        self._save_portfolio()
        
        return {
            'success': True,
            'message': f'{symbol} {shares}주 매수 완료 (${price:.2f})',
            'remaining_cash': self.portfolio['cash']
        }
    
    def remove_position(self, symbol: str, shares: int, price: float, date: str = None):
        """포지션 제거 (매도)"""
        
        if date is None:
            date = datetime.now().isoformat()
        
        # 보유 확인
        if symbol not in self.portfolio['holdings']:
            return {
                'success': False,
                'message': f'{symbol} 미보유'
            }
        
        holding = self.portfolio['holdings'][symbol]
        
        if shares > holding['shares']:
            return {
                'success': False,
                'message': f'보유량 부족: {holding["shares"]}주 < {shares}주'
            }
        
        proceeds = shares * price
        cost_basis = holding['avg_price'] * shares
        profit = proceeds - cost_basis
        
        # 보유량 업데이트
        holding['shares'] -= shares
        holding['total_cost'] -= cost_basis
        
        if holding['shares'] == 0:
            del self.portfolio['holdings'][symbol]
        
        # 현금 증가
        self.portfolio['cash'] += proceeds
        
        # 거래 기록
        self.portfolio['transactions'].append({
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'proceeds': proceeds,
            'profit': profit,
            'date': date
        })
        
        self._save_portfolio()
        
        return {
            'success': True,
            'message': f'{symbol} {shares}주 매도 완료 (${price:.2f})',
            'profit': profit,
            'remaining_cash': self.portfolio['cash']
        }
    
    def get_current_value(self) -> Dict:
        """현재 포트폴리오 가치"""
        
        total_stock_value = 0
        holdings_detail = []
        
        for symbol, holding in self.portfolio['holdings'].items():
            # 현재 시세
            quote = self._get_quote(symbol)
            current_price = quote.get('price', 0) if quote else 0
            
            current_value = holding['shares'] * current_price
            cost_basis = holding['total_cost']
            profit = current_value - cost_basis
            profit_pct = (profit / cost_basis * 100) if cost_basis > 0 else 0
            
            total_stock_value += current_value
            
            holdings_detail.append({
                'symbol': symbol,
                'shares': holding['shares'],
                'avg_price': holding['avg_price'],
                'current_price': current_price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'profit': profit,
                'profit_pct': profit_pct
            })
        
        total_value = self.portfolio['cash'] + total_stock_value
        
        return {
            'cash': self.portfolio['cash'],
            'stock_value': total_stock_value,
            'total_value': total_value,
            'holdings': holdings_detail,
            'allocation': {
                'cash_pct': self.portfolio['cash'] / total_value * 100 if total_value > 0 else 100,
                'stock_pct': total_stock_value / total_value * 100 if total_value > 0 else 0
            }
        }
    
    def get_performance(self) -> Dict:
        """수익률 분석"""
        
        current = self.get_current_value()
        
        # 초기 자본 (첫 거래 전 현금 + 모든 매수 cost)
        initial_cash = 100000  # 기본값
        total_invested = sum(t['cost'] for t in self.portfolio['transactions'] if t['type'] == 'BUY')
        
        total_profit = current['total_value'] - initial_cash
        total_return_pct = (total_profit / initial_cash * 100) if initial_cash > 0 else 0
        
        return {
            'initial_capital': initial_cash,
            'current_value': current['total_value'],
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'best_performer': self._get_best_performer(current['holdings']),
            'worst_performer': self._get_worst_performer(current['holdings'])
        }
    
    def _get_best_performer(self, holdings: List[Dict]) -> Dict:
        """최고 수익 종목"""
        if not holdings:
            return None
        
        return max(holdings, key=lambda x: x['profit_pct'])
    
    def _get_worst_performer(self, holdings: List[Dict]) -> Dict:
        """최저 수익 종목"""
        if not holdings:
            return None
        
        return min(holdings, key=lambda x: x['profit_pct'])
    
    def _get_quote(self, symbol: str) -> Dict:
        """시세 조회"""
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data[0] if data else None
        except:
            return None
    
    def get_summary(self) -> str:
        """포트폴리오 요약 (텔레그램용)"""
        
        current = self.get_current_value()
        performance = self.get_performance()
        
        summary = f"""
💼 **포트폴리오 현황**

📊 **총 평가액**: ${current['total_value']:,.2f}
💰 현금: ${current['cash']:,.2f} ({current['allocation']['cash_pct']:.1f}%)
📈 주식: ${current['stock_value']:,.2f} ({current['allocation']['stock_pct']:.1f}%)

📈 **수익률**
총 수익: ${performance['total_profit']:,.2f}
수익률: {performance['total_return_pct']:+.2f}%

🏆 **보유 종목** ({len(current['holdings'])}개)
"""
        
        for holding in sorted(current['holdings'], key=lambda x: x['current_value'], reverse=True):
            emoji = "🟢" if holding['profit'] > 0 else "🔴" if holding['profit'] < 0 else "⚪"
            summary += f"\n{emoji} **{holding['symbol']}**: {holding['shares']}주"
            summary += f"\n   ${holding['current_price']:.2f} | "
            summary += f"수익: ${holding['profit']:,.2f} ({holding['profit_pct']:+.2f}%)"
        
        if performance['best_performer']:
            best = performance['best_performer']
            summary += f"\n\n🥇 최고: {best['symbol']} ({best['profit_pct']:+.2f}%)"
        
        if performance['worst_performer']:
            worst = performance['worst_performer']
            summary += f"\n🥉 최저: {worst['symbol']} ({worst['profit_pct']:+.2f}%)"
        
        return summary


# ===== 테스트 =====
if __name__ == "__main__":
    pm = PortfolioManager()
    
    # 테스트: 초기 매수
    print("=== 포트폴리오 매니저 테스트 ===\n")
    
    # 샘플 포지션 추가 (테스트)
    if not pm.portfolio['holdings']:
        print("초기 포트폴리오 구성...\n")
        pm.add_position('AAPL', 10, 150.0)
        pm.add_position('MSFT', 15, 380.0)
        pm.add_position('NVDA', 5, 500.0)
    
    # 현재 상태
    print(pm.get_summary())
    
    print("\n✅ 포트폴리오 관리 시스템 작동 완료")