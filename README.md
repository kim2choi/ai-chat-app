# AI Investment Committee System

헤지펀드 투자위원회 구조를 모방한 **멀티 에이전트 AI 투자 분석 시스템**입니다.

텔레그램 명령어 하나로 종합 투자 보고서를 자동 생성합니다.

## 주요 기능

- **멀티 에이전트 분석**: 4개의 전문 AI 팀이 독립적으로 분석
  - 매크로 경제 분석
  - 기술적 분석 (차트, 모멘텀)
  - 종목 발굴 (스크리닝)
  - 펀더멘털 분석 (재무제표)
- **CIO 에이전트**: 4개 팀의 분석을 종합하여 최종 투자 의견 도출
- **텔레그램 봇 연동**: 실시간 명령어로 분석 요청 및 보고서 수신
- **포트폴리오 관리**: 리밸런싱, 리스크 평가, 매매 실행

## 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot Interface                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Investment Committee (CIO)                 │
│                 최종 의사결정 및 보고서 생성                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Macro Team   │   │  Technical    │   │  Fundamental  │
│  매크로 경제   │   │  기술적 분석   │   │  펀더멘털     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Stock Screener│   │   Portfolio   │   │    Order      │
│   종목 발굴    │   │   Manager     │   │   Executor    │
└───────────────┘   └───────────────┘   └───────────────┘
```

## 기술 스택

- **Language**: Python 3.9+
- **AI**: OpenAI GPT-4o API
- **Data**: Financial Modeling Prep API, 한국투자증권 API
- **Interface**: python-telegram-bot (비동기)
- **Techniques**: RAG 패턴, API Rate Limiting, 캐싱

## 설치 및 실행

### 1. 레포지토리 클론

```bash
git clone https://github.com/kim2choi/ai-investment.git
cd ai-investment
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일 생성 후 API 키 입력:

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
FMP_API_KEY=your_financial_modeling_prep_api_key
KIS_APP_KEY=your_korea_investment_app_key
KIS_APP_SECRET=your_korea_investment_app_secret
```

### 4. 텔레그램 봇 실행

```bash
python telegram_trading_bot.py
```

## 프로젝트 구조

```
ai-investment/
├── telegram_bot.py          # 텔레그램 봇 메인
├── telegram_trading_bot.py  # 트레이딩 통합 봇
├── investment_committee.py  # CIO 에이전트 (최종 의사결정)
├── analyst_team.py          # 분석팀 에이전트
├── ai_analyst.py            # AI 분석 코어
├── stock_screener.py        # 종목 스크리닝
├── portfolio_screener.py    # 포트폴리오 스크리닝
├── portfolio_manager.py     # 포트폴리오 관리
├── rebalancer.py            # 리밸런싱 로직
├── order_executor.py        # 매매 실행
├── kis_connector.py         # 한국투자증권 API 연동
├── decision_parser.py       # 의사결정 파싱
├── daily_analysis.py        # 일일 분석
├── multi_stocks.py          # 다중 종목 처리
├── stock_test.py            # 테스트
├── chatbot.html             # 웹 인터페이스
├── data/                    # 데이터 저장 (권장)
│   ├── portfolio.json
│   ├── stock_data_*.json
│   └── committee_decision_*.json
├── requirements.txt
├── .env.example
└── README.md
```

## 사용 예시

### 텔레그램 명령어

```
/analyze AAPL        # 단일 종목 분석
/screen              # 종목 스크리닝
/portfolio           # 포트폴리오 현황
/rebalance           # 리밸런싱 제안
/report              # 종합 투자 보고서 생성
```

### 출력 예시

```
📊 투자위원회 종합 보고서

[매크로 분석]
- 금리 동결 기조 유지, 인플레이션 안정화 추세
- 기술주 중심 상승 모멘텀 지속

[기술적 분석]
- AAPL: RSI 62, 상승 추세 유지
- 지지선 $178, 저항선 $195

[펀더멘털 분석]
- PER 28.5, 업종 평균 대비 적정
- FCF 마진 25%, 재무 건전성 양호

[CIO 최종 의견]
✅ 매수 의견 (신뢰도 78%)
목표가: $195 | 손절가: $170
```

## 개발 배경

군 복무 중 동기들이 감정적이고 투기적인 투자로 손실을 입는 것을 보고, 데이터 기반의 객관적인 투자 판단을 도와주는 시스템을 만들고자 시작했습니다.

사이버지식정보방이라는 제한된 환경에서 독학으로 개발했습니다.

## 향후 계획

- [ ] 백테스팅 시스템 구축
- [ ] 감정 분석 (뉴스, SNS) 통합
- [ ] 멀티모달 데이터 처리
- [ ] 웹 대시보드 개발

## License

MIT License

## Author

[kim2choi](https://github.com/kim2choi)
