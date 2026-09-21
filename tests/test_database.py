"""
Unit tests for SQLite Database operations (services/database.py).
"""
import os
import pytest
import sqlite3
from services.database import (
    init_database,
    save_forecasts,
    get_all_forecasts_df,
    get_available_time_slots,
    get_database_stats,
    get_db_connection
)


@pytest.fixture
def temp_db(tmp_path):
    """建立測試用暫時 SQLite 資料庫路徑。"""
    db_file = tmp_path / "test_weather.db"
    db_path = str(db_file)
    init_database(db_path)
    return db_path


def test_init_database(temp_db):
    """測試資料庫建立與 22 縣市基礎種子資料。"""
    with get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locations")
        count = cursor.fetchone()[0]
        assert count == 22

        cursor.execute("SELECT location_name FROM locations WHERE location_name = '臺中市'")
        row = cursor.fetchone()
        assert row is not None


def test_save_and_query_forecasts(temp_db):
    """測試預報寫入與依條件查詢。"""
    test_data = [
        {
            "dataset_id": "F-C0032-001",
            "location_name": "臺中市",
            "start_time": "2026-09-21T18:00:00+08:00",
            "end_time": "2026-09-22T06:00:00+08:00",
            "wx": "晴時多雲",
            "pop": 10.0,
            "min_t": 25.0,
            "max_t": 30.0,
            "ci": "舒適",
            "fetched_at": "2026-09-21T18:00:00+08:00"
        },
        {
            "dataset_id": "F-C0032-001",
            "location_name": "台北市",  # 測試自動正規化為臺北市
            "start_time": "2026-09-21T18:00:00+08:00",
            "end_time": "2026-09-22T06:00:00+08:00",
            "wx": "多雲短暫雨",
            "pop": 30.0,
            "min_t": 24.0,
            "max_t": 29.0,
            "ci": "舒適",
            "fetched_at": "2026-09-21T18:00:00+08:00"
        }
    ]

    saved = save_forecasts(test_data, db_path=temp_db)
    assert saved == 2

    # 查詢全部
    df = get_all_forecasts_df(db_path=temp_db)
    assert len(df) == 2
    assert "臺北市" in df["location_name"].values

    # 依縣市查詢
    df_tc = get_all_forecasts_df(location_name="台中市", db_path=temp_db)
    assert len(df_tc) == 1
    assert df_tc.iloc[0]["location_name"] == "臺中市"


def test_upsert_behavior(temp_db):
    """測試 UPSERT 重複寫入不增加筆數，但能正確更新數據與時間戳記。"""
    initial_record = [{
        "dataset_id": "F-C0032-001",
        "location_name": "高雄市",
        "start_time": "2026-09-21T18:00:00+08:00",
        "end_time": "2026-09-22T06:00:00+08:00",
        "wx": "晴天",
        "pop": 0.0,
        "min_t": 26.0,
        "max_t": 31.0,
        "ci": "悶熱",
        "fetched_at": "2026-09-21T18:00:00+08:00"
    }]
    save_forecasts(initial_record, db_path=temp_db)

    stats1 = get_database_stats(db_path=temp_db)
    assert stats1["total_records"] == 1

    # 更新同一時段但氣溫與降雨機率改變
    updated_record = [{
        "dataset_id": "F-C0032-001",
        "location_name": "高雄市",
        "start_time": "2026-09-21T18:00:00+08:00",
        "end_time": "2026-09-22T06:00:00+08:00",
        "wx": "多雲短暫陣雨",
        "pop": 50.0,
        "min_t": 27.0,
        "max_t": 33.0,
        "ci": "悶熱易中暑",
        "fetched_at": "2026-09-21T19:00:00+08:00"
    }]
    save_forecasts(updated_record, db_path=temp_db)

    stats2 = get_database_stats(db_path=temp_db)
    assert stats2["total_records"] == 1  # 總筆數不增加

    df = get_all_forecasts_df(location_name="高雄市", db_path=temp_db)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["wx"] == "多雲短暫陣雨"
    assert row["pop"] == 50.0
    assert row["max_t"] == 33.0
    assert row["fetched_at"] == "2026-09-21T19:00:00+08:00"


def test_available_time_slots(temp_db):
    """測試查詢可用預報時段。"""
    records = [
        {
            "dataset_id": "F-C0032-001",
            "location_name": "臺南市",
            "start_time": "2026-09-21T18:00:00+08:00",
            "end_time": "2026-09-22T06:00:00+08:00",
            "wx": "晴天", "pop": 0.0, "min_t": 25.0, "max_t": 30.0, "ci": "舒適",
            "fetched_at": "2026-09-21T18:00:00+08:00"
        },
        {
            "dataset_id": "F-C0032-001",
            "location_name": "臺南市",
            "start_time": "2026-09-22T06:00:00+08:00",
            "end_time": "2026-09-22T18:00:00+08:00",
            "wx": "午後雷陣雨", "pop": 40.0, "min_t": 26.0, "max_t": 33.0, "ci": "悶熱",
            "fetched_at": "2026-09-21T18:00:00+08:00"
        }
    ]
    save_forecasts(records, db_path=temp_db)
    slots = get_available_time_slots(db_path=temp_db)
    assert len(slots) == 2


def test_database_rollback_on_error(temp_db):
    """測試資料庫交易發生錯誤時之 rollback 機制。"""
    with pytest.raises(sqlite3.OperationalError):
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO locations (location_name) VALUES ('測試縣市')")
            # 觸發無效語法以引發例外
            cursor.execute("INSERT INTO non_existent_table VALUES (123)")

    # 驗證 '測試縣市' 未被永久寫入
    with get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locations WHERE location_name = '測試縣市'")
        count = cursor.fetchone()[0]
        assert count == 0
