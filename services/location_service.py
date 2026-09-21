"""
Location Service
管理台灣 22 縣市之基本資料、WGS84 座標、行政代碼以及名稱正規化。
"""
from typing import Dict, List, Optional, Tuple

# 台灣 22 縣市標準資料 (WGS84 經緯度中心點)
TAIWAN_COUNTIES: Dict[str, Dict[str, any]] = {
    "臺北市": {"county_code": "63000", "lat": 25.0375, "lon": 121.5637, "region": "北部"},
    "新北市": {"county_code": "65000", "lat": 24.9157, "lon": 121.6739, "region": "北部"},
    "基隆市": {"county_code": "10017", "lat": 25.1276, "lon": 121.7392, "region": "北部"},
    "桃園市": {"county_code": "68000", "lat": 24.9936, "lon": 121.3010, "region": "北部"},
    "新竹市": {"county_code": "10018", "lat": 24.8138, "lon": 120.9675, "region": "北部"},
    "新竹縣": {"county_code": "10004", "lat": 24.7033, "lon": 121.1252, "region": "北部"},
    "苗栗縣": {"county_code": "10005", "lat": 24.5602, "lon": 120.8214, "region": "中部"},
    "臺中市": {"county_code": "66000", "lat": 24.1477, "lon": 120.6736, "region": "中部"},
    "彰化縣": {"county_code": "10007", "lat": 24.0518, "lon": 120.5161, "region": "中部"},
    "南投縣": {"county_code": "10008", "lat": 23.9609, "lon": 120.9719, "region": "中部"},
    "雲林縣": {"county_code": "10009", "lat": 23.7092, "lon": 120.4313, "region": "中部"},
    "嘉義市": {"county_code": "10020", "lat": 23.4800, "lon": 120.4491, "region": "南部"},
    "嘉義縣": {"county_code": "10010", "lat": 23.4518, "lon": 120.2555, "region": "南部"},
    "臺南市": {"county_code": "67000", "lat": 22.9997, "lon": 120.2270, "region": "南部"},
    "高雄市": {"county_code": "64000", "lat": 22.6273, "lon": 120.3014, "region": "南部"},
    "屏東縣": {"county_code": "10013", "lat": 22.5519, "lon": 120.5487, "region": "南部"},
    "宜蘭縣": {"county_code": "10002", "lat": 24.7021, "lon": 121.7377, "region": "東部"},
    "花蓮縣": {"county_code": "10015", "lat": 23.9871, "lon": 121.6016, "region": "東部"},
    "臺東縣": {"county_code": "10014", "lat": 22.7583, "lon": 121.1444, "region": "東部"},
    "澎湖縣": {"county_code": "10016", "lat": 23.5712, "lon": 119.5793, "region": "離島"},
    "金門縣": {"county_code": "09020", "lat": 24.4492, "lon": 118.3766, "region": "離島"},
    "連江縣": {"county_code": "09007", "lat": 26.1505, "lon": 119.9499, "region": "離島"},
}

# 名稱替代對照表（常見異體字與簡稱）
LOCATION_ALIASES: Dict[str, str] = {
    "台北市": "臺北市",
    "台北": "臺北市",
    "臺北": "臺北市",
    "台中市": "臺中市",
    "台中": "臺中市",
    "臺中": "臺中市",
    "台南市": "臺南市",
    "台南": "臺南市",
    "臺南": "臺南市",
    "台東縣": "臺東縣",
    "台東市": "臺東縣",
    "台東": "臺東縣",
    "臺東": "臺東縣",
    "基隆": "基隆市",
    "新北": "新北市",
    "桃園": "桃園市",
    "新竹": "新竹市",
    "苗栗": "苗栗縣",
    "彰化": "彰化縣",
    "南投": "南投縣",
    "雲林": "雲林縣",
    "嘉義": "嘉義市",
    "高雄": "高雄市",
    "屏東": "屏東縣",
    "宜蘭": "宜蘭縣",
    "花蓮": "花蓮縣",
    "澎湖": "澎湖縣",
    "金門": "金門縣",
    "連江": "連江縣",
    "馬祖": "連江縣",
}


def normalize_location_name(name: Optional[str]) -> Optional[str]:
    """
    將縣市名稱正規化為標準全稱（包含「台」轉「臺」）。
    若輸入為 None 或空字串，回傳 None。
    """
    if not name:
        return None
    cleaned = name.strip()
    if cleaned in TAIWAN_COUNTIES:
        return cleaned
    
    # 檢查別名表
    if cleaned in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned]
    
    # 替換一般「台」為「臺」後再次檢查
    normalized = cleaned.replace("台", "臺")
    if normalized in TAIWAN_COUNTIES:
        return normalized
    if normalized in LOCATION_ALIASES:
        return LOCATION_ALIASES[normalized]
        
    return cleaned


def get_all_locations() -> List[str]:
    """回傳所有 22 個縣市名稱清單（預設臺中市排首位或標準排序）。"""
    return list(TAIWAN_COUNTIES.keys())


def get_location_coordinates(name: str) -> Optional[Tuple[float, float]]:
    """回傳指定縣市的 (緯度 lat, 經度 lon)。"""
    norm_name = normalize_location_name(name)
    if norm_name and norm_name in TAIWAN_COUNTIES:
        info = TAIWAN_COUNTIES[norm_name]
        return (info["lat"], info["lon"])
    return None


def get_location_info(name: str) -> Optional[Dict[str, any]]:
    """回傳指定縣市的完整資訊字典。"""
    norm_name = normalize_location_name(name)
    if norm_name and norm_name in TAIWAN_COUNTIES:
        return TAIWAN_COUNTIES[norm_name]
    return None
