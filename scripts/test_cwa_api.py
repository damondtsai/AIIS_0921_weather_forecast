"""
Test CWA API Connectivity
測試中央氣象署 API 連線狀態（絕不洩漏 API Key）。
"""
import os
import sys

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cwa_client import get_cwa_api_key, fetch_forecast_data


def main():
    print("[*] 正在測試 CWA API 設定與連線...")
    key = get_cwa_api_key()
    if key:
        print("[+] 已偵測到 CWA_API_KEY 環境變數 (長度: %d 字元，金鑰已隱藏)" % len(key))
    else:
        print("[!] 尚未設定有效之 CWA_API_KEY，將以本地 Demo Data 測試。")

    data, status, msg = fetch_forecast_data()
    print(f"\n[*] 測試結果: [{status.upper()}]")
    print(f"[*] 訊息: {msg}")

    if data and "records" in data:
        locs = data["records"].get("location", [])
        print(f"[+] 成功讀取 {len(locs)} 個縣市氣象資料！")
    else:
        print("[!] 無法取得氣象紀錄。")


if __name__ == "__main__":
    main()
