"""
這是一個獨立的檢察工具，唯一的功能就是查詢資料庫並且回傳最新的紀錄數據
"""

import pymongo
from bson.objectid import ObjectId
import datetime

# --- 資料庫設定 ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sensor_data"
COLLECTION_NAME = "spectrograms"  # 您想查詢的集合，可以是 "spectrograms" 或 "measurements"

def check_latest_record():
    """
    連接到 MongoDB 並查詢指定集合中的最新一筆紀錄。
    """
    try:
        # 1. 建立連接
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # 檢查連接是否成功
        client.admin.command('ismaster')
        print(f"成功連接到 MongoDB: {MONGO_URI}")
        
        # 2. 選擇資料庫和集合
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # 3. 查詢最新的一筆資料
        # MongoDB 的 _id 欄位本身就包含了時間戳，所以按 _id 降序排序即可找到最新的紀錄
        latest_record = collection.find_one(sort=[('_id', pymongo.DESCENDING)])
        
        # 4. 顯示結果
        if latest_record:
            print(f"\n在 '{COLLECTION_NAME}' 集合中找到最新一筆紀錄:")
            
            # 格式化輸出，使其更易讀
            for key, value in latest_record.items():
                if isinstance(value, list) and len(value) > 10:
                    # 如果是長列表 (如頻譜數據)，只顯示摘要
                    print(f"  - {key}: [列表，包含 {len(value)} 個元素]")
                elif isinstance(value, datetime.datetime):
                    print(f"  - {key}: {value.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                else:
                    print(f"  - {key}: {value}")
        else:
            print(f"在 '{COLLECTION_NAME}' 集合中沒有找到任何紀錄。")
            
    except pymongo.errors.ConnectionFailure as e:
        print(f"錯誤：無法連接到 MongoDB。請確認您的 MongoDB 服務正在運行中。")
        print(f"詳細資訊: {e}")
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")
    finally:
        # 5. 關閉連接
        if 'client' in locals() and client:
            client.close()
            print("\n資料庫連接已關閉。")

if __name__ == "__main__":
    check_latest_record()

