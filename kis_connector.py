import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

class KISConnector:
    """한국투자증권 API 연동 - 소수점 주식 지원"""
    
    def __init__(self):
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")
        self.account_code = os.getenv("KIS_ACCOUNT_CODE")
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
    
    def get_access_token(self):
        """OAuth 토큰 발급"""
        if self.access_token:
            return self.access_token
        
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result['access_token']
            return self.access_token
        else:
            raise Exception(f"토큰 발급 실패: {response.text}")
    
    def get_all_us_stocks(self):
        """모든 미국 주식 조회 (거래소별)"""
        exchanges = ["NASD", "NYSE", "AMEX"]
        all_stocks = []
        
        print("📊 거래소별 조회 중...")
        for exchange in exchanges:
            try:
                print(f"   - {exchange}...", end=" ")
                stocks = self._get_balance_by_exchange(exchange)
                print(f"{len(stocks)}개 포지션")
                all_stocks.extend(stocks)
            except Exception as e:
                print(f"실패: {e}")
                continue
        
        return all_stocks
    
    def _get_balance_by_exchange(self, exchange_code):
        """특정 거래소 잔고 조회"""
        token = self.get_access_token()
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "TTTS3012R",
            "custtype": "P"
        }
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_code,
            "OVRS_EXCG_CD": exchange_code,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 디버깅: 거래소별 상세
            print(f"\n      === {exchange_code} 상세 ===")
            if 'output1' in data:
                for stock in data['output1']:
                    symbol = stock['ovrs_pdno']
                    shares = stock['ovrs_cblc_qty']
                    name = stock['ovrs_item_name']
                    print(f"      {symbol}: {shares}주 ({name})")
            print()
            
            if 'output1' in data:
                return data['output1']
        
        return []
    
    def parse_portfolio(self):
        """포트폴리오 파싱 (소수점 주식, 중복 제거)"""
        all_stocks = self.get_all_us_stocks()
        
        print(f"✅ 총 {len(all_stocks)}개 포지션 발견\n")
        
        # 중복 제거
        unique_stocks = {}
        for stock in all_stocks:
            symbol = stock['ovrs_pdno']
            if symbol not in unique_stocks:
                unique_stocks[symbol] = stock
        
        print(f"중복 제거 후: {len(unique_stocks)}개 고유 종목\n")
        
        portfolio = {
            'cash': 0,
            'holdings': {},
            'total_value': 0
        }
        
        for symbol, stock in unique_stocks.items():
            shares = float(stock['ovrs_cblc_qty'])
            
            if shares > 0:
                portfolio['holdings'][symbol] = {
                    'name': stock['ovrs_item_name'],
                    'shares': shares,
                    'avg_price': float(stock['pchs_avg_pric']),
                    'current_price': float(stock['now_pric2']),
                    'total_cost': shares * float(stock['pchs_avg_pric']),
                    'current_value': shares * float(stock['now_pric2']),
                    'profit': shares * (float(stock['now_pric2']) - float(stock['pchs_avg_pric'])),
                    'profit_pct': ((float(stock['now_pric2']) - float(stock['pchs_avg_pric'])) / float(stock['pchs_avg_pric']) * 100),
                    'exchange': stock['ovrs_excg_cd']
                }
        
        stock_value = sum(h['current_value'] for h in portfolio['holdings'].values())
        portfolio['total_value'] = stock_value
        portfolio['cash'] = 0
        
        return portfolio
    
    def sync_to_portfolio_manager(self, pm):
        """PortfolioManager와 동기화"""
        real_portfolio = self.parse_portfolio()
        
        pm.portfolio['cash'] = real_portfolio['cash']
        pm.portfolio['holdings'] = {}
        
        for symbol, data in real_portfolio['holdings'].items():
            pm.portfolio['holdings'][symbol] = {
                'shares': data['shares'],
                'avg_price': data['avg_price'],
                'total_cost': data['total_cost'],
                'first_purchase': datetime.now().isoformat()
            }
        
        pm.save()
        return real_portfolio


if __name__ == "__main__":
    print("=" * 70)
    print("한국투자증권 API - 실전 포트폴리오")
    print("=" * 70)
    
    kis = KISConnector()
    
    try:
        print("\n1. OAuth 토큰 발급 중...")
        token = kis.get_access_token()
        print(f"✅ 토큰 발급 완료\n")
        
        print("2. 전체 거래소 잔고 조회...")
        portfolio = kis.parse_portfolio()
        
        print("=" * 70)
        print("💼 실전 포트폴리오")
        print("=" * 70)
        print(f"\n📊 총 평가액: ${portfolio['total_value']:,.2f}")
        print(f"📈 보유 종목: {len(portfolio['holdings'])}개\n")
        
        print("-" * 70)
        
        for symbol, data in sorted(portfolio['holdings'].items(), 
                                   key=lambda x: x[1]['current_value'], 
                                   reverse=True):
            profit_emoji = "🟢" if data['profit'] > 0 else "🔴" if data['profit'] < 0 else "⚪"
            
            print(f"{profit_emoji} {symbol} ({data['exchange']})")
            print(f"   {data['name']}")
            print(f"   보유: {data['shares']:.6f}주")
            print(f"   평균가: ${data['avg_price']:.2f}")
            print(f"   현재가: ${data['current_price']:.2f}")
            print(f"   평가액: ${data['current_value']:.2f}")
            print(f"   수익: ${data['profit']:.2f} ({data['profit_pct']:+.2f}%)")
            print()
        
        print("=" * 70)
        print("✅ API 연동 완료!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()