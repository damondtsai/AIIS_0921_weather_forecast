"""
Fetch CWA Weather Forecast Script
抓取中央氣象署最新預報資料，解析並以 UPSERT 方式寫入 SQLite 資料庫。
"""
import os
import sys

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cwa_client import fetch_forecast_data
from services.cwa_parser import parse_cwa_response
from services.database import save_forecasts, get_database_stats


def main():
    print("[*] 開始抓取中央氣象署 (CWA) 氣象預報資料...")
    data, status, message = fetch_forecast_data()
    print(f"[*] 資料來源狀態: [{status.upper()}] - {message}")

    if not data:
        print("[!] 未取得有效資料，程式結束。")
        return

    print("[*] 正在解析 JSON 資料...")
    forecasts = parse_cwa_response(data)
    print(f"[*] 共解析出 {len(forecasts)} 筆各縣市時段預報紀錄。")

    print("[*] 正在寫入 SQLite 資料庫 (UPSERT)...")
    saved_count = save_forecasts(forecasts)
    print(f"[+] 成功更新/儲存 {saved_count} 筆預報紀錄！")

    stats = get_database_stats()
    print("\n========== 資料庫最新狀態 ==========")
    print(f"總資料筆數: {stats['total_records']}")
    print(f"涵蓋縣市數: {stats['locations_count']}")
    print(f"最早預報時間: {stats['earliest_forecast']}")
    print(f"最晚預報時間: {stats['latest_forecast']}")
    print(f"最後更新時間: {stats['last_fetched_at']}")
    print("=====================================")


if __name__ == "__main__":
    main()
