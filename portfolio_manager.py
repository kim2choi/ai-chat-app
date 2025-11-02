import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class PortfolioManager:
    """포트폴리오 관리자"""
    
    def __init__(self, portfolio_file: str = "portfolio.json"):
        self.portfolio_file = portfolio_file
        self.portfolio = self._load_portfolio()
    
    def _load_portfolio(self) -> Dict:
        """포트폴리오 불러오기"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"포트폴리오 로드 실패: {e}")
        
        # 기본 포트폴리오
        return {
            "cash": 0,
            "holdings": {},
            "transactions": [],
            "created_at": datetime.now().isoformat()
        }
    
    def save(self):
        """포트폴리오를 파일에 저장"""
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=2)
    
    def get_current_value(self) -> Dict:
        """현재 포트폴리오 가치 조회"""
        total_stock_value = 0
        holdings_list = []
        
        for symbol, data in self.portfolio['holdings'].items():
            holding_info = {
                'symbol': symbol,
                'shares': data['shares'],
                'avg_price': data['avg_price'],
                'current_price': data.get('current_price', data['avg_price']),
                'current_value': data['shares'] * data.get('current_price', data['avg_price']),
                'cost_basis': data['shares'] * data['avg_price'],
                'profit': (data.get('current_price', data['avg_price']) - data['avg_price']) * data['shares'],
                'profit_pct': ((data.get('current_price', data['avg_price']) / data['avg_price']) - 1) * 100
            }
            total_stock_value += holding_info['current_value']
            holdings_list.append(holding_info)
        
        return {
            'cash': self.portfolio['cash'],
            'stock_value': total_stock_value,
            'total_value': self.portfolio['cash'] + total_stock_value,
            'holdings': holdings_list
        }
    
    def update_holding(self, symbol: str, shares: float, price: float, current_price: Optional[float] = None):
        """보유 종목 업데이트"""
        if symbol not in self.portfolio['holdings']:
            self.portfolio['holdings'][symbol] = {
                'shares': 0,
                'avg_price': 0,
                'current_price': price
            }
        
        holding = self.portfolio['holdings'][symbol]
        
        # 평균 단가 계산
        total_cost = holding['shares'] * holding['avg_price'] + shares * price
        total_shares = holding['shares'] + shares
        
        if total_shares > 0:
            holding['avg_price'] = total_cost / total_shares
            holding['shares'] = total_shares
            holding['current_price'] = current_price if current_price else price
        else:
            # 전량 매도
            del self.portfolio['holdings'][symbol]
        
        self.save()
    
    def set_holding(self, symbol: str, shares: float, avg_price: float, current_price: float):
        """보유 종목 직접 설정 (동기화용)"""
        if shares > 0:
            self.portfolio['holdings'][symbol] = {
                'shares': shares,
                'avg_price': avg_price,
                'current_price': current_price
            }
        elif symbol in self.portfolio['holdings']:
            del self.portfolio['holdings'][symbol]
    
    def set_cash(self, amount: float):
        """현금 설정"""
        self.portfolio['cash'] = amount
    
    def add_transaction(self, transaction: Dict):
        """거래 기록 추가"""
        transaction['timestamp'] = datetime.now().isoformat()
        self.portfolio['transactions'].append(transaction)
        self.save()
    
    def get_transactions(self, limit: int = 10) -> List[Dict]:
        """최근 거래 내역 조회"""
        return self.portfolio['transactions'][-limit:]
    
    def clear_holdings(self):
        """모든 보유 종목 삭제"""
        self.portfolio['holdings'] = {}
        self.save()
    
    def get_holding(self, symbol: str) -> Optional[Dict]:
        """특정 종목 조회"""
        return self.portfolio['holdings'].get(symbol)
    
    def has_holding(self, symbol: str) -> bool:
        """종목 보유 여부"""
        return symbol in self.portfolio['holdings'] and self.portfolio['holdings'][symbol]['shares'] > 0


if __name__ == "__main__":
    # 테스트
    pm = PortfolioManager()
    
    print("현재 포트폴리오:")
    current = pm.get_current_value()
    print(f"총 평가액: ${current['total_value']:,.2f}")
    print(f"현금: ${current['cash']:,.2f}")
    print(f"주식: ${current['stock_value']:,.2f}")
    
    print("\n보유 종목:")
    for holding in current['holdings']:
        print(f"{holding['symbol']}: {holding['shares']:.4f}주 @ ${holding['current_price']:.2f}")
        print(f"  수익: ${holding['profit']:.2f} ({holding['profit_pct']:+.2f}%)")