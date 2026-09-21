"""
Weather Table Component (CWA V8 Style)
呈現全台 22 縣市分區天氣預報表格，支援北部/中部/南部/東部/離島快速分頁檢視。
"""
from typing import Optional
import pandas as pd
import streamlit as st
from services.location_service import TAIWAN_COUNTIES


def render_weather_table(forecast_df: pd.DataFrame) -> None:
    """呈現 CWA 官方風格的各縣市預報表格。"""
    if forecast_df.empty:
        st.info("目前資料庫中無氣象預報資料。")
        return

    df = forecast_df.copy()

    # 加入區域分組
    df["區域"] = df["location_name"].apply(lambda name: TAIWAN_COUNTIES.get(name, {}).get("region", "其他"))
    df["縣市"] = df["location_name"]
    df["開始時間"] = df["start_time"].str.replace("T", " ").str.slice(0, 16)
    df["結束時間"] = df["end_time"].str.replace("T", " ").str.slice(0, 16)
    df["天氣現象"] = df["wx"].fillna("未知")
    df["最低溫 (°C)"] = df["min_t"].apply(lambda v: f"{v:.1f}" if pd.notnull(v) else "--")
    df["最高溫 (°C)"] = df["max_t"].apply(lambda v: f"{v:.1f}" if pd.notnull(v) else "--")
    df["降雨機率"] = df["pop"].apply(lambda v: f"{int(v)}%" if pd.notnull(v) else "--")
    df["舒適度"] = df["ci"].fillna("無")
    df["更新時間"] = df["fetched_at"].str.replace("T", " ").str.slice(0, 19)

    display_cols = [
        "區域", "縣市", "開始時間", "結束時間", "天氣現象",
        "最低溫 (°C)", "最高溫 (°C)", "降雨機率", "舒適度", "更新時間"
    ]

    # 分區 Tabs
    tab_all, tab_north, tab_central, tab_south, tab_east, tab_islands = st.tabs([
        "🌐 全台 22 縣市", "🌲 北部地區", "🌿 中部地區", "☀️ 南部地區", "🌊 東部地區", "🏝️ 離島地區"
    ])

    with tab_all:
        st.dataframe(df[display_cols], width="stretch", hide_index=True, height=360)

    with tab_north:
        df_n = df[df["區域"] == "北部"]
        st.dataframe(df_n[display_cols], width="stretch", hide_index=True, height=300)

    with tab_central:
        df_c = df[df["區域"] == "中部"]
        st.dataframe(df_c[display_cols], width="stretch", hide_index=True, height=300)

    with tab_south:
        df_s = df[df["區域"] == "南部"]
        st.dataframe(df_s[display_cols], width="stretch", hide_index=True, height=300)

    with tab_east:
        df_e = df[df["區域"] == "東部"]
        st.dataframe(df_e[display_cols], width="stretch", hide_index=True, height=300)

    with tab_islands:
        df_i = df[df["區域"] == "離島"]
        st.dataframe(df_i[display_cols], width="stretch", hide_index=True, height=300)
