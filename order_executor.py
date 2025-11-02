import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from kis_connector import KISConnector
from portfolio_manager import PortfolioManager
import json

load_dotenv()

class OrderExecutor:
    """주문 실행 엔진 - 실제 매매"""
    
    def __init__(self):
        self.kis = KISConnector()
        self.pm = PortfolioManager()
        
        # 안전장치 설정
        self.max_order_value = 10000  # 최대 주문 금액 $10,000
        self.max_position_pct = 0.3    # 최대 포지션 비중 30%
        self.min_cash_reserve = 100    # 최소 현금 보유 $100
    
    def validate_order(self, symbol: str, quantity: int, price: float, order_type: str) -> Dict:
        """주문 검증"""
        
        issues = []
        warnings = []
        
        # 1. 주문 금액 체크
        order_value = quantity * price
        if order_value > self.max_order_value:
            issues.append(f"주문 금액 ${order_value:.2f} > 최대 ${self.max_order_value}")
        
        # 2. 현재 포트폴리오 조회
        current = self.pm.get_current_value()
        
        if order_type == "BUY":
            # 매수 검증
            if order_value > current['cash']:
                issues.append(f"현금 부족: ${current['cash']:.2f} < ${order_value:.2f}")
            
            if current['cash'] - order_value < self.min_cash_reserve:
                warnings.append(f"최소 현금({self.min_cash_reserve}) 미달 가능")
            
            # 포지션 비중 체크
            future_position_value = order_value
            for holding in current['holdings']:
                if holding['symbol'] == symbol:
                    future_position_value += holding['current_value']
            
            future_pct = future_position_value / (current['total_value'] + order_value)
            if future_pct > self.max_position_pct:
                warnings.append(f"종목 비중 {future_pct*100:.1f}% > 최대 {self.max_position_pct*100}%")
        
        elif order_type == "SELL":
            # 매도 검증
            holding = self.pm.get_holding(symbol)
            if not holding:
                issues.append(f"{symbol} 보유하지 않음")
            elif holding['shares'] < quantity:
                issues.append(f"보유 수량 부족: {holding['shares']} < {quantity}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'order_value': order_value
        }
    
    def execute_buy(self, symbol: str, quantity: int) -> Dict:
        """매수 주문"""
        
        print(f"\n{'='*60}")
        print(f"💰 매수 주문: {symbol} {quantity}주")
        print(f"{'='*60}")
        
        try:
            # 1. 현재 가격 조회
            # (한투 API로 실시간 가격 조회하는 코드 - 일단 간단히)
            price = 100.0  # TODO: 실제 가격 조회 구현
            
            # 2. 검증
            validation = self.validate_order(symbol, quantity, price, "BUY")
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation
                }
            
            if validation['warnings']:
                print("⚠️  경고:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
            
            # 3. 실제 주문 (한투 API)
            print(f"\n📤 한투 API 주문 전송 중...")
            
            result = self.kis.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type="BUY"
            )
            
            # 4. 포트폴리오 업데이트
            if result['success']:
                self.pm.update_holding(
                    symbol=symbol,
                    shares=quantity,
                    price=result['executed_price']
                )
                
                print(f"✅ 매수 체결!")
                print(f"   종목: {symbol}")
                print(f"   수량: {quantity}주")
                print(f"   가격: ${result['executed_price']:.2f}")
                print(f"   총액: ${result['executed_price'] * quantity:.2f}")
            
            return result
            
        except Exception as e:
            print(f"❌ 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_sell(self, symbol: str, quantity: int) -> Dict:
        """매도 주문"""
        
        print(f"\n{'='*60}")
        print(f"💵 매도 주문: {symbol} {quantity}주")
        print(f"{'='*60}")
        
        try:
            # 1. 현재 가격 조회
            price = 100.0  # TODO: 실제 가격 조회
            
            # 2. 검증
            validation = self.validate_order(symbol, quantity, price, "SELL")
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation
                }
            
            # 3. 실제 주문
            print(f"\n📤 한투 API 주문 전송 중...")
            
            result = self.kis.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type="SELL"
            )
            
            # 4. 포트폴리오 업데이트
            if result['success']:
                self.pm.update_holding(
                    symbol=symbol,
                    shares=-quantity,
                    price=result['executed_price']
                )
                
                print(f"✅ 매도 체결!")
                print(f"   종목: {symbol}")
                print(f"   수량: {quantity}주")
                print(f"   가격: ${result['executed_price']:.2f}")
                print(f"   총액: ${result['executed_price'] * quantity:.2f}")
            
            return result
            
        except Exception as e:
            print(f"❌ 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_rebalancing(self, decision: Dict) -> Dict:
        """리밸런싱 결정 실행"""
        
        print(f"\n{'='*80}")
        print(f"🏛️  CIO 결정 실행")
        print(f"{'='*80}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'buys': [],
            'sells': [],
            'errors': []
        }
        
        # CIO 결정 파싱
        # TODO: CIO 결정서에서 매수/매도 추출
        
        print("\n⚠️  실제 주문 전 최종 확인이 필요합니다!")
        print("텔레그램 봇의 /execute 명령어를 사용하세요.")
        
        return results


# ═══════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    executor = OrderExecutor()
    
    print("주문 실행 엔진 테스트")
    print("=" * 60)
    
    # 검증 테스트
    validation = executor.validate_order("AAPL", 10, 150.0, "BUY")
    print(f"\n검증 결과: {validation}")