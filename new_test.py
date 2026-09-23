import pymongo
import certifi
from dotenv import load_dotenv
import os
# from NgxStockPrediction.data_inventory import NGXStockDataExtract


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

# ngx_api_key=os.getenv("NGX_API_KEY")
# ngxStockDataExtract=NGXStockDataExtract()

# tickers_list=[]
# for file in os.listdir('each_stock_model_notebook'):
#     stock_symbol=file.split('_')[0]
#     tickers_list.append(stock_symbol)

# print(tickers_list)
# print(len(tickers_list))

# ngxStockDataExtract.get_stock_data_from_ngx_pulse(tickers=tickers_list, ngx_api_key=ngx_api_key)

# # Connect to your Atlas cluster to PULL THE UNIQUE SYMBOLS
# db = client["NGX_Stock_ME_Database"]
# collection = db["stock_data"]

# # Option 1: distinct() - simplest, returns a plain list
# symbols = collection.distinct("symbol")
# print(symbols)
# print(f"Total unique symbols: {len(symbols)}")


unique_symbols_in_mongodb=[None, 'ABBEYBANK', 'ABCTRANS', 'ACADEMY', 'ACCESSCORP', 'AFRINSURE', 'AFRIPRUD', 'AFROMEDIA', 'AIICO', 'AIRTELAFRI', 'ALEX', 'ARADEL', 'AUSTINLAZ', 'AVAIF', 'BAPLC', 'BERGER', 'BETAGLAS', 'BUACEMENT', 'BUAFOODS', 'CADBURY', 'CAP', 'CAVERTON', 'CHAMPION', 'CHAMS', 'CHELLARAM', 'CMFC', 'CNIF', 'CONHALLPLC', 'CONOIL', 'CORNERST', 'CUSTODIAN', 'CUTIX', 'CWG', 'DAARCOMM', 'DANGCEM', 'DANGSUGAR', 'EKOCORP', 'ELLAHLAKES', 'ENAMELWA', 'ETERNA', 'ETI', 'ETRANZACT', 'EUNISELL', 'FCMB', 'FIDELITYBK', 'FIDSON', 'FIRSTHOLDCO', 'FTGINSURE', 'FTNCOCOA', 'GEREGU', 'GOLDBREW', 'GTCO', 'GUINEAINS', 'GUINNESS', 'HBMNG', 'HMCALL', 'HONYFLOUR', 'IKEJAHOTEL', 'IMG', 'INTBREW', 'INTENEGINS', 'JAIZBANK', 'JAPAULGOLD', 'JBERGER', 'JOHNHOLT', 'JULI', 'LASACO', 'LEARNAFRCA', 'LEGENDINT', 'LINKASSURE', 'LIVESTOCK', 'LIVINGTRUST', 'MANSARD', 'MAYBAKER', 'MBENEFIT', 'MCNICHOLS', 'MECURE', 'MEYER', 'MOFIREIF', 'MORISON', 'MTNN', 'MULTITREX', 'MULTIVERSE', 'NAHCO', 'NASCON', 'NB', 'NCR', 'NEIMETH', 'NEM', 'NESTLE', 'NGXGROUP', 'NIDF', 'NNFM', 'NPFMCRFBK', 'NREIT', 'NSLTECH', 'OANDO', 'OKOMUOIL', 'OMATEK', 'PHARMDEKO', 'PREMPAINTS', 'PRESTIGE', 'PZ', 'REDSTAREX', 'REGALINS', 'RONCHESS', 'ROYALEX', 'RTBRISCOE', 'SCOA', 'SEPLAT', 'SFSREIT', 'SKYAVN', 'SOVRENINS', 'STACO', 'STANBIC', 'STERLINGNG', 'SUNUASSUR', 'TANTALIZER', 'THOMASWY', 'TIP', 'TOTAL', 'TRANSCOHOT', 'TRANSCORP', 'TRANSEXPR', 'TRANSPOWER', 'TRIPPLEG', 'UACN', 'UBA', 'UCAP', 'UHOMREIT', 'UNILEVER', 'UNIONDICON', 'UNITYBNK', 'UNIVINSURE', 'UPDC', 'UPDCREIT', 'UPL', 'VERITASKAP', 'VFDGROUP', 'VITAFOAM', 'WAPIC', 'WEMABANK', 'ZENITHBANK', 'ZICHIS']
