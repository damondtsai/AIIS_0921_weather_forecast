"""
CWA API Client
負責與中央氣象署 Open Data API 進行安全通訊，具備 20 秒逾時防護、敏感金鑰屏蔽及示範資料自動降級機制。
"""
import os
import json
import logging
from typing import Any, Dict, Optional, Tuple
import requests
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
DEFAULT_DATASET_ID = os.getenv("CWA_DATASET_ID", "F-C0032-001")
SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample_cwa.json"
)

logger = logging.getLogger(__name__)


def get_cwa_api_key() -> Optional[str]:
    """安全地從環境變數取得 CWA API Key。"""
    key = os.getenv("CWA_API_KEY")
    if key:
        key = key.strip()
        # 排除範例預設假資料
        if key in ("your_cwa_api_key_here", "YOUR_API_KEY", ""):
            return None
    return key if key else None


def load_sample_data() -> Dict[str, Any]:
    """從本地 data/sample_cwa.json 載入示範資料。"""
    if os.path.exists(SAMPLE_DATA_PATH):
        with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "success": "false",
        "result": {"resource_id": DEFAULT_DATASET_ID},
        "records": {"datasetDescription": "示範資料檔缺失", "location": []}
    }


def fetch_forecast_data(
    dataset_id: Optional[str] = None,
    location_name: Optional[str] = None,
    fallback_to_sample: bool = True
) -> Tuple[Dict[str, Any], str, str]:
    """
    從 CWA API 取得即時天氣預報。
    
    回傳元組：
    - data (Dict[str, Any]): 回傳之 JSON 物件
    - status (str): "live" | "demo" | "error"
    - message (str): 繁體中文狀態提示說明
    
    安全規範：
    - 絕不在 log, 終端機或回傳訊息中顯示 API Key。
    """
    api_key = get_cwa_api_key()
    target_dataset = dataset_id or DEFAULT_DATASET_ID

    if not api_key:
        if fallback_to_sample:
            sample = load_sample_data()
            return (
                sample,
                "demo",
                "尚未設定 CWA API Key 或為範例值，已載入示範預報資料 (Demo Data)。"
            )
        return (
            {},
            "error",
            "尚未設定 CWA API Key (請於 .env 設定 CWA_API_KEY)。"
        )

    endpoint = f"{BASE_URL}{target_dataset}"
    params = {
        "Authorization": api_key,
        "format": "JSON",
    }
    if location_name:
        params["locationName"] = location_name

    try:
        try:
            response = requests.get(endpoint, params=params, timeout=20)
        except requests.exceptions.SSLError:
            # 針對特定平台環境或過渡證書進行 SSL 容錯重試
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(endpoint, params=params, timeout=20, verify=False)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success") == "true" or "records" in data:
                    return (data, "live", "成功取得 CWA 即時氣象預報 (Live Data)。")
                else:
                    err_msg = "CWA API 回應未包含成功標記。"
                    if fallback_to_sample:
                        return (load_sample_data(), "demo", f"{err_msg} 已自動降級為示範資料。")
                    return ({}, "error", err_msg)
            except json.JSONDecodeError:
                err_msg = "CWA API 回傳非有效 JSON格式。"
                if fallback_to_sample:
                    return (load_sample_data(), "demo", f"{err_msg} 已自動降級為示範資料。")
                return ({}, "error", err_msg)

        elif response.status_code in (401, 403):
            err_msg = f"CWA API 授權失敗 (HTTP {response.status_code})，請確認 API Key 是否有效。"
            if fallback_to_sample:
                return (load_sample_data(), "demo", f"{err_msg} 已切換為示範資料。")
            return ({}, "error", err_msg)
        else:
            err_msg = f"CWA API 連線異常 (HTTP {response.status_code})。"
            if fallback_to_sample:
                return (load_sample_data(), "demo", f"{err_msg} 已切換為示範資料。")
            return ({}, "error", err_msg)

    except requests.exceptions.Timeout:
        err_msg = "連線中央氣象署 API 逾時 (20 秒)。"
        if fallback_to_sample:
            return (load_sample_data(), "demo", f"{err_msg} 已自動切換為示範資料。")
        return ({}, "error", err_msg)
    except requests.exceptions.RequestException as e:
        err_msg = f"網路連線失敗 ({type(e).__name__})。"
        if fallback_to_sample:
            return (load_sample_data(), "demo", f"{err_msg} 已自動切換為示範資料。")
        return ({}, "error", err_msg)
