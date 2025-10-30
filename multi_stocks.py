import requests
import json
from datetime import datetime

api_key = "FqMw8Dk6AcYH5a6R2RMBctcE7f9yJCEL"
symbols = ["AAPL", "TSLA", "MSFT", "NVDA"]

results = []

for symbol in symbols:
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
    response = requests.get(url)
    data = response.json()[0]
    
    results.append({
        "symbol": data["symbol"],
        "name": data["name"],
        "price": data["price"],
        "change_percent": data["changesPercentage"]
    })
    
    print(f"{data['symbol']}: ${data['price']} ({data['changesPercentage']}%)")

# 파일로 저장
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"stock_data_{timestamp}.json"

with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n데이터 저장됨: {filename}")
