import requests
import os
from dotenv import load_dotenv

load_dotenv()

ngx_api_key=os.getenv("NGX_API_KEY")

ngx_market_url = "https://www.ngxpulse.ng/api/ngxdata/market"
ngx_stocks_url = "https://www.ngxpulse.ng/api/ngxdata/stocks"

headers = {
    "X-API-Key": f"{ngx_api_key}",
    "Content-Type": "application/json"
}

response = requests.get(ngx_stocks_url, headers=headers)

print(response.status_code)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(response.text)