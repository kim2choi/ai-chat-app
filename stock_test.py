import requests
import json

api_key = "FqMw8Dk6AcYH5a6R2RMBctcE7f9yJCEL"
symbol = "AAPL"

url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"

response = requests.get(url)
data = response.json()

print(f"회사: {data[0]['name']}")
print(f"가격: ${data[0]['price']}")
print(f"변동: {data[0]['changesPercentage']}%")
