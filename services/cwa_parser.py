"""
CWA JSON Parser
解析中央氣象署 F-C0032-001 (一般天氣預報 - 今明 36 小時預報) JSON 資料。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import pytz
import pandas as pd

from services.location_service import normalize_location_name

TAIPEI_TZ = pytz.timezone("Asia/Taipei")


def _to_float(val: Any) -> Optional[float]:
    """安全地將數值轉為 float，若失敗則回傳 None。"""
    if val is None:
        return None
    try:
        s = str(val).strip()
        if not s or s.lower() == "none" or s == "-":
            return None
        return float(s)
    except (ValueError, TypeError):
        return None


def _format_iso_time(time_str: str) -> str:
    """
    將 CWA 常見時間格式 (e.g. '2026-09-21 18:00:00' 或 ISO 字串) 轉為標準 ISO 8601 格式字串。
    """
    if not time_str or not isinstance(time_str, str):
        return ""
    cleaned = time_str.strip()
    try:
        # 常見格式: 'YYYY-MM-DD HH:MM:SS'
        if " " in cleaned and "T" not in cleaned:
            dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        elif "T" in cleaned:
            # ISO 格式
            dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        else:
            return cleaned
            
        # 若無時區資訊，賦予台北時區
        if dt.tzinfo is None:
            dt = TAIPEI_TZ.localize(dt)
        return dt.isoformat()
    except Exception:
        return cleaned


def parse_cwa_response(
    raw_data: Any,
    dataset_id: str = "F-C0032-001",
    fetched_at: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    解析 CWA API 回傳之 JSON 資料（或已 json.loads 的 dict），轉換為標準平坦化預報清單。
    
    支援結構防護：
    - 依據 elementName 查找，不依賴陣列順序。
    - 以 (startTime, endTime) 作為時間鍵正確對齊 Wx, PoP, MinT, MaxT, CI。
    - 容錯缺失欄位與數值轉換。
    """
    if not isinstance(raw_data, dict):
        return []

    # 取得抓取時間
    if not fetched_at:
        fetched_at = datetime.now(TAIPEI_TZ).isoformat()
    else:
        fetched_at = _format_iso_time(fetched_at)

    records = raw_data.get("records")
    if not isinstance(records, dict):
        return []

    locations = records.get("location")
    if not isinstance(locations, list):
        return []

    forecast_results: List[Dict[str, Any]] = []

    for loc in locations:
        if not isinstance(loc, dict):
            continue

        raw_location_name = loc.get("locationName")
        norm_location_name = normalize_location_name(raw_location_name)
        if not norm_location_name:
            continue

        weather_elements = loc.get("weatherElement")
        if not isinstance(weather_elements, list):
            continue

        # 整理此縣市各時間區段的氣象元素: time_slots[(start, end)] = {elem_name: val}
        # 鍵值: (start_time_iso, end_time_iso)
        time_slots: Dict[tuple, Dict[str, Any]] = {}

        for elem in weather_elements:
            if not isinstance(elem, dict):
                continue
            elem_name = elem.get("elementName", "").strip()
            times = elem.get("time")
            if not isinstance(times, list):
                continue

            for t in times:
                if not isinstance(t, dict):
                    continue
                start_raw = t.get("startTime", "")
                end_raw = t.get("endTime", "")
                if not start_raw or not end_raw:
                    continue

                start_iso = _format_iso_time(start_raw)
                end_iso = _format_iso_time(end_raw)
                time_key = (start_iso, end_iso)

                if time_key not in time_slots:
                    time_slots[time_key] = {
                        "Wx": None,
                        "PoP": None,
                        "MinT": None,
                        "MaxT": None,
                        "CI": None,
                    }

                param = t.get("parameter", {})
                param_name = param.get("parameterName") if isinstance(param, dict) else None

                # 根據 elementName 映射
                if elem_name == "Wx":
                    time_slots[time_key]["Wx"] = str(param_name).strip() if param_name is not None else None
                elif elem_name in ("PoP", "PoP12h", "PoP24h"):
                    time_slots[time_key]["PoP"] = _to_float(param_name)
                elif elem_name == "MinT":
                    time_slots[time_key]["MinT"] = _to_float(param_name)
                elif elem_name == "MaxT":
                    time_slots[time_key]["MaxT"] = _to_float(param_name)
                elif elem_name == "CI":
                    time_slots[time_key]["CI"] = str(param_name).strip() if param_name is not None else None

        # 轉成標準預報物件清單
        for (start_time, end_time), data in sorted(time_slots.items(), key=lambda x: x[0][0]):
            forecast_results.append({
                "dataset_id": dataset_id,
                "location_name": norm_location_name,
                "start_time": start_time,
                "end_time": end_time,
                "wx": data["Wx"],
                "pop": data["PoP"],
                "min_t": data["MinT"],
                "max_t": data["MaxT"],
                "ci": data["CI"],
                "fetched_at": fetched_at,
            })

    return forecast_results


def parse_to_dataframe(
    raw_data: Any,
    dataset_id: str = "F-C0032-001",
    fetched_at: Optional[str] = None
) -> pd.DataFrame:
    """將 CWA API 回傳資料直接解析為 Pandas DataFrame。"""
    parsed_list = parse_cwa_response(raw_data, dataset_id=dataset_id, fetched_at=fetched_at)
    if not parsed_list:
        return pd.DataFrame(columns=[
            "dataset_id", "location_name", "start_time", "end_time",
            "wx", "pop", "min_t", "max_t", "ci", "fetched_at"
        ])
    return pd.DataFrame(parsed_list)
