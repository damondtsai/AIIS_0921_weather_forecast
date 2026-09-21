"""
Unit tests for CWA JSON Parser (services/cwa_parser.py).
"""
import pytest
import os
import json
from services.cwa_parser import parse_cwa_response, parse_to_dataframe
from services.location_service import normalize_location_name


@pytest.fixture
def sample_json():
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "sample_cwa.json"
    )
    with open(sample_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_normal_json_parsing(sample_json):
    """測試正常 JSON 解析邏輯。"""
    results = parse_cwa_response(sample_json)
    assert len(results) > 0

    # 驗證必要欄位存在
    first = results[0]
    expected_keys = {
        "dataset_id", "location_name", "start_time", "end_time",
        "wx", "pop", "min_t", "max_t", "ci", "fetched_at"
    }
    assert expected_keys.issubset(first.keys())
    assert isinstance(first["min_t"], (int, float))
    assert isinstance(first["max_t"], (int, float))
    assert isinstance(first["pop"], (int, float))


def test_missing_elements():
    """測試缺少某些氣象元素時不崩潰並填入 None。"""
    raw_data = {
        "success": "true",
        "records": {
            "location": [
                {
                    "locationName": "臺中市",
                    "weatherElement": [
                        {
                            "elementName": "Wx",
                            "time": [
                                {
                                    "startTime": "2026-09-21 18:00:00",
                                    "endTime": "2026-09-22 06:00:00",
                                    "parameter": {"parameterName": "晴時多雲"}
                                }
                            ]
                        }
                        # 故意缺少 PoP, MinT, MaxT, CI
                    ]
                }
            ]
        }
    }
    results = parse_cwa_response(raw_data)
    assert len(results) == 1
    r = results[0]
    assert r["wx"] == "晴時多雲"
    assert r["pop"] is None
    assert r["min_t"] is None
    assert r["max_t"] is None
    assert r["ci"] is None


def test_empty_locations():
    """測試 records 或 location 為空的情況。"""
    assert parse_cwa_response({}) == []
    assert parse_cwa_response({"records": {}}) == []
    assert parse_cwa_response({"records": {"location": []}}) == []
    assert parse_cwa_response("invalid string") == []


def test_invalid_numeric_values():
    """測試氣象數值為無效字串或異常符號時的安全轉換。"""
    raw_data = {
        "records": {
            "location": [
                {
                    "locationName": "臺北市",
                    "weatherElement": [
                        {
                            "elementName": "MinT",
                            "time": [
                                {
                                    "startTime": "2026-09-21 18:00:00",
                                    "endTime": "2026-09-22 06:00:00",
                                    "parameter": {"parameterName": "N/A"}
                                }
                            ]
                        },
                        {
                            "elementName": "PoP",
                            "time": [
                                {
                                    "startTime": "2026-09-21 18:00:00",
                                    "endTime": "2026-09-22 06:00:00",
                                    "parameter": {"parameterName": "-"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    results = parse_cwa_response(raw_data)
    assert len(results) == 1
    assert results[0]["min_t"] is None
    assert results[0]["pop"] is None


def test_element_order_independence():
    """測試氣象元素在陣列中順序調換時依然正確解析對齊。"""
    raw_data = {
        "records": {
            "location": [
                {
                    "locationName": "高雄市",
                    "weatherElement": [
                        # MaxT 在最前，Wx 在最後
                        {
                            "elementName": "MaxT",
                            "time": [{"startTime": "2026-09-21 18:00:00", "endTime": "2026-09-22 06:00:00", "parameter": {"parameterName": "32"}}]
                        },
                        {
                            "elementName": "MinT",
                            "time": [{"startTime": "2026-09-21 18:00:00", "endTime": "2026-09-22 06:00:00", "parameter": {"parameterName": "26"}}]
                        },
                        {
                            "elementName": "Wx",
                            "time": [{"startTime": "2026-09-21 18:00:00", "endTime": "2026-09-22 06:00:00", "parameter": {"parameterName": "晴天"}}]
                        }
                    ]
                }
            ]
        }
    }
    results = parse_cwa_response(raw_data)
    assert len(results) == 1
    r = results[0]
    assert r["max_t"] == 32.0
    assert r["min_t"] == 26.0
    assert r["wx"] == "晴天"


def test_location_name_normalization():
    """測試「台」與「臺」以及別名之正規化轉換。"""
    assert normalize_location_name("台北市") == "臺北市"
    assert normalize_location_name("台中市") == "臺中市"
    assert normalize_location_name("台南市") == "臺南市"
    assert normalize_location_name("台東縣") == "臺東縣"
    assert normalize_location_name("台中") == "臺中市"
    assert normalize_location_name("臺北市") == "臺北市"
    assert normalize_location_name(None) is None


def test_parse_to_dataframe(sample_json):
    """測試 parse_to_dataframe 輸出 DataFrame 結構。"""
    df = parse_to_dataframe(sample_json)
    assert not df.empty
    assert "location_name" in df.columns
    assert "max_t" in df.columns
    assert "min_t" in df.columns
