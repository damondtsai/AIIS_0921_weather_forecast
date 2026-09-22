import { createClient, Client } from "@libsql/client";
import { ForecastRecord } from "./types";

let clientInstance: Client | null = null;

export function getDb(): Client {
  if (!clientInstance) {
    const url = process.env.DATABASE_URL || "file:weather.db";
    const authToken = process.env.DATABASE_AUTH_TOKEN || undefined;

    clientInstance = createClient({
      url,
      authToken,
    });
  }
  return clientInstance;
}

export async function initDb(): Promise<void> {
  const db = getDb();
  await db.executeMultiple(`
    CREATE TABLE IF NOT EXISTS forecasts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_name TEXT NOT NULL,
      start_time TEXT NOT NULL,
      end_time TEXT NOT NULL,
      weather TEXT,
      weather_code TEXT,
      pop INTEGER,
      min_t REAL,
      max_t REAL,
      comfort TEXT,
      fetched_at TEXT NOT NULL,
      UNIQUE(location_name, start_time, end_time)
    );
    CREATE INDEX IF NOT EXISTS idx_forecasts_location_start
    ON forecasts(location_name, start_time);
  `);
}

export async function upsertForecasts(records: ForecastRecord[]): Promise<number> {
  const db = getDb();
  await initDb();

  if (!records || records.length === 0) return 0;

  let insertedCount = 0;
  // Use transaction/batch for performance and atomicity
  const statements = records.map((r) => ({
    sql: `
      INSERT INTO forecasts (
        location_name, start_time, end_time, weather, weather_code,
        pop, min_t, max_t, comfort, fetched_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(location_name, start_time, end_time)
      DO UPDATE SET
        weather = excluded.weather,
        weather_code = excluded.weather_code,
        pop = excluded.pop,
        min_t = excluded.min_t,
        max_t = excluded.max_t,
        comfort = excluded.comfort,
        fetched_at = excluded.fetched_at;
    `,
    args: [
      r.location_name,
      r.start_time,
      r.end_time,
      r.weather,
      r.weather_code || null,
      r.pop ?? null,
      r.min_t ?? null,
      r.max_t ?? null,
      r.comfort || null,
      r.fetched_at,
    ],
  }));

  // Batch execute in chunks of 50 to avoid hitting batch limits
  const chunkSize = 50;
  for (let i = 0; i < statements.length; i += chunkSize) {
    const chunk = statements.slice(i, i + chunkSize);
    await db.batch(chunk, "write");
    insertedCount += chunk.length;
  }

  return insertedCount;
}

export async function queryForecasts(locationName?: string): Promise<ForecastRecord[]> {
  const db = getDb();
  await initDb();

  if (locationName) {
    const result = await db.execute({
      sql: `
        SELECT * FROM forecasts 
        WHERE location_name = ? 
        ORDER BY start_time ASC
        LIMIT 6;
      `,
      args: [locationName],
    });
    return result.rows as unknown as ForecastRecord[];
  }

  const result = await db.execute(`
    SELECT * FROM forecasts 
    ORDER BY location_name ASC, start_time ASC;
  `);
  return result.rows as unknown as ForecastRecord[];
}
