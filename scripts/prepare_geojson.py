"""
Prepare and clean Taiwan Counties GeoJSON with accurate attributes.
"""
import os
import sys
import json
import requests

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.location_service import TAIWAN_COUNTIES

URL = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/master/public/data/taiwan.geojson"

NAME_MAP = {
    "Taipei City": "臺北市",
    "Taoyuan County": "桃園市",
    "Taoyuan City": "桃園市",
    "Taichung City": "臺中市",
    "Tainan City": "臺南市",
    "Keelung City": "基隆市",
    "Nantou County": "南投縣",
    "Yilan County": "宜蘭縣",
    "Chiayi City": "嘉義市",
    "Miaoli County": "苗栗縣",
    "Kaohsiung City": "高雄市",
    "Hsinchu City": "新竹市",
    "Hsinchu County": "新竹縣",
    "Kinmen County": "金門縣",
    "Changhua County": "彰化縣",
    "Penghu County": "澎湖縣",
    "New Taipei City": "新北市",
    "Chiayi County": "嘉義縣",
    "Pingtung County": "屏東縣",
    "Yunlin County": "雲林縣",
    "Hualien County": "花蓮縣",
    "Lienchiang County": "連江縣",
    "Taitung County": "臺東縣",
}

def main():
    os.makedirs("data", exist_ok=True)
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    cleaned_features = []
    for feat in data.get("features", []):
        raw_name = feat.get("properties", {}).get("name", "").strip()
        c_name = NAME_MAP.get(raw_name, raw_name)
        info = TAIWAN_COUNTIES.get(c_name, {})
        feat["properties"] = {
            "COUNTYNAME": c_name,
            "name": c_name,
            "COUNTYCODE": info.get("county_code", ""),
            "name_en": raw_name,
            "lat": info.get("lat"),
            "lon": info.get("lon"),
            "region": info.get("region", "")
        }
        cleaned_features.append(feat)

    data["features"] = cleaned_features

    output_path = os.path.join("data", "taiwan_counties.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"GeoJSON saved successfully to {output_path} with {len(cleaned_features)} features.")

if __name__ == "__main__":
    main()
