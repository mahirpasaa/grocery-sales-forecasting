"""Feature engineering for the store x family daily sales panel.

Design choice: every history-based feature is lagged by at least HORIZON (16) days, so a single
model can forecast all 16 days of the horizon without ever seeing data from inside it
("direct" multi-horizon setup, no recursive error accumulation and no leakage).
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = (ROOT / "data" / "parquet").as_posix()

HORIZON = 16
START = "2015-06-01"   # before this, several families are only recorded every other month (see EDA)
LAGS = [16, 21, 28, 35, 42, 364]
ROLL_WINDOWS = [7, 14, 28, 56, 112]
CATEGORICAL = ["store_nbr", "family", "store_type", "cluster", "city"]


def load_panel() -> pd.DataFrame:
    """Complete store x family x date grid (train + test period), with store and holiday info."""
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    df = con.execute(f"""
        WITH obs AS (
            SELECT date, store_nbr, family, sales, onpromotion FROM '{PARQUET}/sales.parquet'
            UNION ALL
            SELECT date, store_nbr, family, NULL, onpromotion  FROM '{PARQUET}/test.parquet'
        ),
        cal AS (
            SELECT CAST(range AS DATE) AS date
            FROM range(DATE '{START}', (SELECT MAX(date) FROM obs) + 1, INTERVAL 1 DAY)
        ),
        series AS (SELECT DISTINCT store_nbr, family FROM obs),
        hol AS (
            SELECT date, locale, locale_name
            FROM '{PARQUET}/holidays.parquet'
            WHERE type IN ('Holiday', 'Transfer', 'Additional', 'Bridge') AND NOT transferred
        )
        SELECT c.date, s.store_nbr, s.family,
               o.sales,
               COALESCE(o.onpromotion, 0)                                   AS onpromotion,
               st.type AS store_type, st.cluster, st.city,
               EXISTS (SELECT 1 FROM hol h WHERE h.date = c.date AND h.locale = 'National')          AS hol_national,
               EXISTS (SELECT 1 FROM hol h WHERE h.date = c.date AND h.locale_name IN (st.city, st.state)
                                              AND h.locale IN ('Local', 'Regional'))                  AS hol_local,
               (month(c.date) = 12 AND day(c.date) = 25)                    AS closed
        FROM cal c
        CROSS JOIN series s
        LEFT JOIN obs o ON o.date = c.date AND o.store_nbr = s.store_nbr AND o.family = s.family
        JOIN '{PARQUET}/stores.parquet' st ON st.store_nbr = s.store_nbr
        ORDER BY s.store_nbr, s.family, c.date
    """).df()
    df.loc[df.closed, "sales"] = 0.0
    df["date"] = pd.to_datetime(df["date"])
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag/rolling/calendar features. `df` must be sorted by series then date."""
    df = df.copy()
    df["y"] = np.log1p(df["sales"].clip(lower=0)).astype("float32")
    g = df.groupby(["store_nbr", "family"], sort=False)

    for lag in LAGS:
        df[f"lag_{lag}"] = g["y"].shift(lag).astype("float32")

    base = g["y"].shift(HORIZON)
    gb = base.groupby([df.store_nbr, df.family], sort=False)
    for w in ROLL_WINDOWS:
        df[f"roll_mean_{w}"] = gb.transform(lambda s: s.rolling(w, min_periods=1).mean()).astype("float32")
    df["roll_std_28"] = gb.transform(lambda s: s.rolling(28, min_periods=7).std()).astype("float32")
    df["zero_share_56"] = (base == 0).astype("float32").groupby([df.store_nbr, df.family], sort=False) \
        .transform(lambda s: s.rolling(56, min_periods=1).mean()).astype("float32")

    # Same weekday, last four available weeks (lags 21..42 are all multiples of 7 >= HORIZON).
    df["same_dow_mean_4w"] = df[["lag_21", "lag_28", "lag_35", "lag_42"]].mean(axis=1).astype("float32")

    # Promotions are planned in advance, so the current value is known at forecast time.
    df["promo_log"] = np.log1p(df["onpromotion"]).astype("float32")
    promo_hist = g["onpromotion"].shift(HORIZON).groupby([df.store_nbr, df.family], sort=False) \
        .transform(lambda s: s.rolling(28, min_periods=1).mean())
    df["promo_vs_usual"] = (df["onpromotion"] / (promo_hist + 1)).astype("float32")

    d = df["date"]
    df["dow"] = d.dt.dayofweek.astype("int8")
    df["dom"] = d.dt.day.astype("int8")
    df["month"] = d.dt.month.astype("int8")
    df["doy"] = d.dt.dayofyear.astype("int16")
    df["days_to_month_end"] = (d.dt.days_in_month - d.dt.day).astype("int8")
    df["payday"] = ((d.dt.day == 15) | d.dt.is_month_end).astype("int8")
    df["hol_national"] = df["hol_national"].astype("int8")
    df["hol_local"] = df["hol_local"].astype("int8")

    for c in CATEGORICAL:
        df[c] = df[c].astype("category")
    return df


FEATURES = (
    CATEGORICAL
    + [f"lag_{l}" for l in LAGS]
    + [f"roll_mean_{w}" for w in ROLL_WINDOWS]
    + ["roll_std_28", "zero_share_56", "same_dow_mean_4w",
       "onpromotion", "promo_log", "promo_vs_usual",
       "dow", "dom", "month", "doy", "days_to_month_end", "payday", "hol_national", "hol_local"]
)
