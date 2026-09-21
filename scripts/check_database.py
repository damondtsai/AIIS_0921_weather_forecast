"""
Check Database Script
檢查 SQLite 資料庫健康狀態並輸出統計數據。
"""
import os
import sys

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.database import DEFAULT_DB_PATH, get_database_stats


def main():
    print(f"[*] 檢查資料庫狀態: {DEFAULT_DB_PATH}")
    if not os.path.exists(DEFAULT_DB_PATH):
        print(f"[!] 資料庫檔案尚未建立，請先執行: python scripts/init_db.py")
        return

    stats = get_database_stats()
    print("\n========== SQLite 資料庫統計報表 ==========")
    print(f"總資料筆數: {stats['total_records']}")
    print(f"縣市數量: {stats['locations_count']}")
    print(f"最早預報時間: {stats['earliest_forecast'] or '無'}")
    print(f"最晚預報時間: {stats['latest_forecast'] or '無'}")
    print(f"缺少 MinT 或 MaxT 的筆數: {stats['missing_temp_count']}")
    print(f"最後資料更新時間: {stats['last_fetched_at'] or '無'}")
    print("============================================")


if __name__ == "__main__":
    main()
