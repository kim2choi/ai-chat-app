import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class KISConnector:
    """한국투자증권 API 연동"""
    
    def __init__(self):
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")
        self.account_code = os.getenv("KIS_ACCOUNT_CODE", "01")
        
        # 실전/모의 구분
        self.base_url = "https://openapi.koreainvestment.com:9443"
        
        # 토큰 캐시
        self._token = None
        self._token_expires = 0
        
        if not all([self.app_key, self.app_secret, self.account_no]):
            raise ValueError("KIS API 키가 .env에 없습니다!")
    
    def _get_access_token(self) -> str:
        """접근 토큰 발급 (캐싱)"""
        
        # 캐시된 토큰이 유효하면 재사용
        if self._token and time.time() < self._token_expires:
            return self._token
        
        url = f"{self.base_url}/oauth2/tokenP"
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if 'access_token' in result:
            self._token = result['access_token']
            # 토큰 유효시간: 24시간 - 안전하게 23시간
            self._token_expires = time.time() + (23 * 60 * 60)
            return self._token
        else:
            raise Exception(f"토큰 발급 실패: {result}")
    
    def get_overseas_balance(self, exchange: str = "NASD") -> Dict:
        """해외 주식 잔고 조회 (현금 포함)"""
        
        token = self._get_access_token()
        
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "TTTS3012R",
            "custtype": "P"
        }
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_code,
            "OVRS_EXCG_CD": exchange,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        
        # 현금 잔고 추출
        cash = 0
        if result.get('rt_cd') == '0' and 'output2' in result:
            output2 = result['output2']
            
            # output2가 list인 경우
            if isinstance(output2, list) and len(output2) > 0:
                cash = float(output2[0].get('frcr_dncl_amt_2', 0))
            # output2가 dict인 경우
            elif isinstance(output2, dict):
                cash = float(output2.get('frcr_dncl_amt_2', 0))
        
        return {
            'result': result,
            'cash': cash
        }
    
    def parse_portfolio(self) -> Dict:
        """포트폴리오 파싱 (여러 거래소 통합 + 현금)"""
        
        print("📊 거래소별 조회 중...")
        
        exchanges = ["NASD", "NYSE", "AMEX"]
        all_holdings = {}
        total_cash = 0
        
        for exchange in exchanges:
            print(f"   - {exchange}... ")
            
            try:
                balance_data = self.get_overseas_balance(exchange)
                data = balance_data['result']
                
                # 현금 (첫 거래소에서만)
                if exchange == "NASD" and balance_data['cash'] > 0:
                    total_cash = balance_data['cash']
                    print(f"      💵 현금: ${total_cash:,.2f}")
                
                if data.get('rt_cd') == '0' and 'output1' in data:
                    holdings = data['output1']
                    
                    print(f"      === {exchange} 상세 ===")
                    
                    for item in holdings:
                        symbol = item['ovrs_pdno']
                        name = item['ovrs_item_name']
                        shares = float(item['ovrs_cblc_qty'])
                        
                        if shares > 0:
                            print(f"      {symbol}: {shares}주 ({name})")
                            
                            if symbol not in all_holdings:
                                all_holdings[symbol] = {
                                    'symbol': symbol,
                                    'name': name,
                                    'shares': 0,
                                    'avg_price': 0,
                                    'current_value': 0
                                }
                            
                            all_holdings[symbol]['shares'] += shares
                            all_holdings[symbol]['avg_price'] = float(item['pchs_avg_pric'])
                            all_holdings[symbol]['current_value'] += float(item['ovrs_stck_evlu_amt'])
                    
                    holding_count = len([h for h in holdings if float(h['ovrs_cblc_qty']) > 0])
                    if holding_count > 0:
                        print(f"      {holding_count}개 포지션")
                
            except Exception as e:
                print(f"      ⚠️  조회 실패: {e}")
        
        print(f"\n✅ 총 {len(all_holdings)}개 고유 종목")
        print(f"💵 현금: ${total_cash:,.2f}\n")
        
        total_value = sum(h['current_value'] for h in all_holdings.values()) + total_cash
        
        return {
            'holdings': all_holdings,
            'cash': total_cash,
            'total_value': total_value,
            'timestamp': datetime.now().isoformat()
        }
    
    def sync_to_portfolio_manager(self, pm) -> Dict:
        """PortfolioManager와 동기화 (현금 포함)"""
        
        portfolio = self.parse_portfolio()
        
        # 기존 보유 종목 초기화
        pm.clear_holdings()
        
        # 현금 설정
        pm.set_cash(portfolio['cash'])
        
        # 새로운 보유 종목 설정
        for symbol, data in portfolio['holdings'].items():
            pm.set_holding(
                symbol=symbol,
                shares=data['shares'],
                avg_price=data['avg_price'],
                current_price=data['avg_price']
            )
        
        # 저장
        pm.save()
        
        return portfolio
    
    def place_order(self, symbol: str, quantity: int, order_type: str) -> Dict:
        """
        실제 주문 실행
        
        Args:
            symbol: 종목 코드
            quantity: 수량
            order_type: "BUY" 또는 "SELL"
        """
        
        try:
            # 1. 접근 토큰
            token = self._get_access_token()
            
            # 2. 주문 구분 코드
            if order_type == "BUY":
                order_code = "TTTT1002U"  # 미국 주식 매수
            elif order_type == "SELL":
                order_code = "TTTT1006U"  # 미국 주식 매도
            else:
                raise ValueError(f"Invalid order_type: {order_type}")
            
            # 3. 주문 데이터
            url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
            
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": order_code,
                "custtype": "P"  # 개인
            }
            
            data = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.account_code,
                "OVRS_EXCG_CD": "NASD",  # 나스닥 (TODO: 종목별로 거래소 구분)
                "PDNO": symbol,
                "ORD_QTY": str(quantity),
                "OVRS_ORD_UNPR": "0",  # 시장가
                "ORD_SVR_DVSN_CD": "0",  # 일반주문
                "ORD_DVSN": "00"  # 지정가 (시장가는 01)
            }
            
            # 4. 주문 전송
            print(f"📤 주문 전송: {order_type} {symbol} {quantity}주")
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            # 5. 결과 처리
            if result['rt_cd'] == '0':  # 성공
                return {
                    'success': True,
                    'order_no': result['output']['ODNO'],
                    'executed_price': float(result['output'].get('AVG_PRVS', 0)),
                    'message': result['msg1']
                }
            else:
                return {
                    'success': False,
                    'error': result['msg1'],
                    'code': result['rt_cd']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_price(self, symbol: str, exchange: str = "NASD") -> Optional[float]:
        """현재 가격 조회"""
        
        try:
            token = self._get_access_token()
            
            url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
            
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "HHDFS00000300",  # 해외주식 현재가
                "custtype": "P"
            }
            
            params = {
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": symbol
            }
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result['rt_cd'] == '0' and 'output' in result:
                return float(result['output']['last'])
            else:
                return None
                
        except Exception as e:
            print(f"가격 조회 실패: {e}")
            return None


# ═══════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    kis = KISConnector()
    
    print("=" * 80)
    print("한국투자증권 API 테스트")
    print("=" * 80)
    
    # 포트폴리오 조회
    portfolio = kis.parse_portfolio()
    
    print("\n💵 현금:")
    print(f"${portfolio['cash']:,.2f}")
    
    print("\n보유 종목:")
    for symbol, data in portfolio['holdings'].items():
        print(f"{symbol}: {data['shares']}주 (${data['current_value']:.2f})")
    
    print(f"\n📊 총 평가액: ${portfolio['total_value']:,.2f}")