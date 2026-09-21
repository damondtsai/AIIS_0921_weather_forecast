"""
Weather Table Component
呈現各縣市完整氣象預報表格，支援排序與欄位格式化。
"""
import pandas as pd
import streamlit as st


def render_weather_table(forecast_df: pd.DataFrame) -> None:
    """
    格式化呈現完整預報資料表。
    
    欄位需求：
    - 縣市
    - 開始時間
    - 結束時間
    - 天氣
    - 最低溫
    - 最高溫
    - 降雨機率
    - 舒適度
    - 資料更新時間
    """
    if forecast_df.empty:
        st.info("目前資料庫中無氣象預報資料。")
        return

    df = forecast_df.copy()

    # 格式化欄位呈現
    df["縣市"] = df["location_name"]
    df["開始時間"] = df["start_time"].str.replace("T", " ").str.slice(0, 16)
    df["結束時間"] = df["end_time"].str.replace("T", " ").str.slice(0, 16)
    df["天氣現象"] = df["wx"].fillna("未知")
    df["最低溫 (°C)"] = df["min_t"].apply(lambda v: f"{v:.1f}" if pd.notnull(v) else "--")
    df["最高溫 (°C)"] = df["max_t"].apply(lambda v: f"{v:.1f}" if pd.notnull(v) else "--")
    df["降雨機率"] = df["pop"].apply(lambda v: f"{int(v)}%" if pd.notnull(v) else "--")
    df["舒適度"] = df["ci"].fillna("無")
    df["資料更新時間"] = df["fetched_at"].str.replace("T", " ").str.slice(0, 19)

    display_cols = [
        "縣市", "開始時間", "結束時間", "天氣現象",
        "最低溫 (°C)", "最高溫 (°C)", "降雨機率",
        "舒適度", "資料更新時間"
    ]

    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        height=420
    )
