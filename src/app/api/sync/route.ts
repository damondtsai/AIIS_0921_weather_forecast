import { NextResponse } from "next/server";
import { fetchCwaWeather, normalizeCwaData } from "@/lib/cwa";
import { upsertForecasts } from "@/lib/db";
import { ApiResponse } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(): Promise<NextResponse<ApiResponse>> {
  try {
    const { data: cwaData, isFallback } = await fetchCwaWeather();
    const records = normalizeCwaData(cwaData);
    const count = await upsertForecasts(records);

    return NextResponse.json({
      ok: true,
      message: isFallback
        ? "已同步本地範例氣象資料 (未設定 CWA_API_KEY 或網路中斷)"
        : "成功同步中央氣象署 (CWA) 最新 36 小時預報資料",
      total: count,
      updatedAt: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "同步氣象資料時發生未知錯誤";
    console.error("Sync error:", error);
    return NextResponse.json(
      {
        ok: false,
        error: `氣象資料同步失敗：${errorMessage}`,
      },
      { status: 500 }
    );
  }
}

export async function GET(): Promise<NextResponse<ApiResponse>> {
  // Support GET trigger for cron jobs or direct browser verification
  return POST();
}
