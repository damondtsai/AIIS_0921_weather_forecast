"""
Database Initialization Script
初始化 SQLite 資料表與台灣 22 縣市基礎座標資料。
"""
import os
import sys

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.database import DEFAULT_DB_PATH, init_database, get_database_stats


def main():
    print(f"[*] 正在初始化 SQLite 資料庫: {DEFAULT_DB_PATH}")
    init_database()
    print("[+] 資料庫結構與 22 縣市地理座標建立完成！")
    
    stats = get_database_stats()
    print(f"[*] 目前狀態：資料表已就緒，預報筆數: {stats['total_records']}")


if __name__ == "__main__":
    main()
