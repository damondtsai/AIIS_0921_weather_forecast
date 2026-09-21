"""
Database Service
處理 SQLite 資料庫連線、資料表建立、UPSERT 操作與統計查詢。
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple
import pandas as pd

from services.location_service import TAIWAN_COUNTIES, normalize_location_name

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "weather.db"
)


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """
    SQLite 資料庫 Context Manager。
    自動管理連線、交易提交與例外 rollback。
    """
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    初始化 SQLite 資料庫結構：
    - locations 資料表
    - weather_forecasts 資料表
    - 唯一索引 (dataset_id, location_name, start_time, end_time)
    - 預填 22 縣市基本地理資訊
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. 建立 locations 資料表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT UNIQUE NOT NULL,
                county_code TEXT,
                latitude REAL,
                longitude REAL
            )
        """)

        # 2. 建立 weather_forecasts 資料表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                location_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                wx TEXT,
                pop REAL,
                min_t REAL,
                max_t REAL,
                ci TEXT,
                fetched_at TEXT NOT NULL
            )
        """)

        # 3. 建立唯一複合索引
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_forecast_unique 
            ON weather_forecasts(dataset_id, location_name, start_time, end_time)
        """)

        # 4. 預填 22 縣市資料 (UPSERT)
        for loc_name, info in TAIWAN_COUNTIES.items():
            cursor.execute("""
                INSERT INTO locations (location_name, county_code, latitude, longitude)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(location_name) DO UPDATE SET
                    county_code=excluded.county_code,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude
            """, (loc_name, info.get("county_code"), info.get("lat"), info.get("lon")))


def save_forecasts(forecasts: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> int:
    """
    將預報清單寫入 SQLite 資料庫 (UPSERT)。
    若已存在相同 (dataset_id, location_name, start_time, end_time)，則更新其氣象值與 fetched_at。
    回傳成功處理筆數。
    """
    if not forecasts:
        return 0

    init_database(db_path)

    upsert_sql = """
        INSERT INTO weather_forecasts (
            dataset_id, location_name, start_time, end_time,
            wx, pop, min_t, max_t, ci, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dataset_id, location_name, start_time, end_time) DO UPDATE SET
            wx = excluded.wx,
            pop = excluded.pop,
            min_t = excluded.min_t,
            max_t = excluded.max_t,
            ci = excluded.ci,
            fetched_at = excluded.fetched_at
    """

    count = 0
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for f in forecasts:
            norm_name = normalize_location_name(f.get("location_name"))
            if not norm_name:
                continue

            cursor.execute(upsert_sql, (
                f.get("dataset_id", "F-C0032-001"),
                norm_name,
                f.get("start_time"),
                f.get("end_time"),
                f.get("wx"),
                f.get("pop"),
                f.get("min_t"),
                f.get("max_t"),
                f.get("ci"),
                f.get("fetched_at")
            ))
            count += 1

    return count


def get_all_forecasts_df(
    dataset_id: str = "F-C0032-001",
    location_name: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> pd.DataFrame:
    """查詢預報紀錄並轉為 DataFrame。"""
    init_database(db_path)
    
    query = """
        SELECT dataset_id, location_name, start_time, end_time,
               wx, pop, min_t, max_t, ci, fetched_at
        FROM weather_forecasts
        WHERE dataset_id = ?
    """
    params = [dataset_id]

    if location_name:
        norm_name = normalize_location_name(location_name)
        query += " AND location_name = ?"
        params.append(norm_name)

    query += " ORDER BY location_name ASC, start_time ASC"

    with get_db_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_available_time_slots(
    dataset_id: str = "F-C0032-001",
    db_path: str = DEFAULT_DB_PATH
) -> List[Tuple[str, str]]:
    """取得目前資料庫中所有預報時段清單 [(start_time, end_time), ...]。"""
    init_database(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT start_time, end_time
            FROM weather_forecasts
            WHERE dataset_id = ?
            ORDER BY start_time ASC
        """, (dataset_id,))
        rows = cursor.fetchall()
        return [(r[0], r[1]) for r in rows]


def get_database_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    取得資料庫健檢統計資訊：
    - 總資料筆數
    - 縣市數量
    - 最早預報時間
    - 最晚預報時間
    - 缺少 MinT 或 MaxT 的筆數
    - 最後資料更新時間
    """
    init_database(db_path)
    stats: Dict[str, Any] = {
        "total_records": 0,
        "locations_count": 0,
        "earliest_forecast": None,
        "latest_forecast": None,
        "missing_temp_count": 0,
        "last_fetched_at": None,
    }

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 總筆數
        cursor.execute("SELECT COUNT(*) FROM weather_forecasts")
        stats["total_records"] = cursor.fetchone()[0]

        # 縣市數量
        cursor.execute("SELECT COUNT(DISTINCT location_name) FROM weather_forecasts")
        stats["locations_count"] = cursor.fetchone()[0]

        # 最早與最晚預報時間
        cursor.execute("SELECT MIN(start_time), MAX(end_time) FROM weather_forecasts")
        row = cursor.fetchone()
        if row:
            stats["earliest_forecast"] = row[0]
            stats["latest_forecast"] = row[1]

        # 缺少 MinT 或 MaxT 的筆數
        cursor.execute("""
            SELECT COUNT(*) FROM weather_forecasts 
            WHERE min_t IS NULL OR max_t IS NULL
        """)
        stats["missing_temp_count"] = cursor.fetchone()[0]

        # 最後資料更新時間
        cursor.execute("SELECT MAX(fetched_at) FROM weather_forecasts")
        row = cursor.fetchone()
        if row:
            stats["last_fetched_at"] = row[0]

    return stats
