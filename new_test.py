import pymongo
import certifi
from dotenv import load_dotenv
import os
from NgxStockPrediction.data_inventory import NGXStockDataExtract


load_dotenv()

# if __name__=="__main__":
#     uri = os.getenv("MONGO_DB_CLUSTER_URL")
#     client = pymongo.MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)

#     try:
#         print(client.admin.command('ping'))
#         print("Connected successfully!")
#     except Exception as e:
#         print("Connection failed:", e)

uri = os.getenv("MONGO_DB_CLUSTER_URL")
client = pymongo.MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)

ngx_api_key=os.getenv("NGX_API_KEY")
ngxStockDataExtract=NGXStockDataExtract()

tickers_list=[]
for file in os.listdir('each_stock_model_notebook'):
    stock_symbol=file.split('_')[0]
    tickers_list.append(stock_symbol)

print(tickers_list)
print(len(tickers_list))

ngxStockDataExtract.get_stock_data_from_ngx_pulse(tickers=tickers_list, ngx_api_key=ngx_api_key)


