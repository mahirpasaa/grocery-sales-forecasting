"""Baselines, LightGBM model, metrics and a rolling-origin backtest."""
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from features import FEATURES, HORIZON

LGB_PARAMS = dict(
    objective="regression",      # on log1p(sales) -> optimises RMSLE
    learning_rate=0.05,
    num_leaves=255,
    min_child_samples=50,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=1,
    lambda_l2=1.0,
    verbose=-1,
    seed=42,
)
N_ROUNDS = 800


# ---------- metrics ----------
def rmsle(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.log1p(y_pred) - np.log1p(y_true)) ** 2)))


def wape(y_true, y_pred) -> float:
    """Weighted absolute percentage error: total absolute error / total actual sales."""
    return float(np.abs(y_true - y_pred).sum() / y_true.sum())


def bias(y_true, y_pred) -> float:
    return float(y_pred.sum() / y_true.sum() - 1)


def score(y_true, y_pred) -> dict:
    return {"RMSLE": rmsle(y_true, y_pred), "WAPE": wape(y_true, y_pred), "Bias": bias(y_true, y_pred)}


# ---------- helpers ----------
def _dead_series(hist: pd.DataFrame) -> pd.Index:
    """Series with no sales in the last 56 days before the cutoff: forecast 0."""
    last = hist[hist.date > hist.date.max() - pd.Timedelta(days=56)]
    s = last.groupby(["store_nbr", "family"], observed=True).sales.sum()
    return s[s == 0].index


def _zero_dead(fc: pd.DataFrame, dead: pd.Index, col: str) -> pd.DataFrame:
    key = pd.MultiIndex.from_frame(fc[["store_nbr", "family"]].astype(object))
    fc.loc[key.isin(dead), col] = 0.0
    return fc


# ---------- models ----------
def seasonal_naive(hist: pd.DataFrame, future: pd.DataFrame) -> np.ndarray:
    """Same weekday of the last observed week."""
    last_week = hist[hist.date > hist.date.max() - pd.Timedelta(days=7)]
    ref = last_week.assign(dow=last_week.date.dt.dayofweek)[["store_nbr", "family", "dow", "sales"]]
    out = future[["store_nbr", "family", "dow"]].merge(ref, on=["store_nbr", "family", "dow"], how="left")
    return out.sales.fillna(0).to_numpy()


def weekday_mean_4w(hist: pd.DataFrame, future: pd.DataFrame) -> np.ndarray:
    """Mean of the same weekday over the last 4 weeks (computed in log space, robust to spikes)."""
    last = hist[hist.date > hist.date.max() - pd.Timedelta(days=28)]
    ref = (last.assign(dow=last.date.dt.dayofweek, ly=np.log1p(last.sales))
               .groupby(["store_nbr", "family", "dow"], observed=True).ly.mean()
               .rename("ly").reset_index())
    out = future[["store_nbr", "family", "dow"]].merge(ref, on=["store_nbr", "family", "dow"], how="left")
    return np.expm1(out.ly.fillna(0)).to_numpy()


def fit_lgb(train: pd.DataFrame) -> lgb.Booster:
    train = train[train.y.notna() & ~train.closed & train.lag_364.notna()]
    ds = lgb.Dataset(train[FEATURES], label=train.y, categorical_feature="auto", free_raw_data=True)
    return lgb.train(LGB_PARAMS, ds, num_boost_round=N_ROUNDS)


def predict_lgb(model: lgb.Booster, future: pd.DataFrame) -> np.ndarray:
    return np.clip(np.expm1(model.predict(future[FEATURES])), 0, None)


# ---------- backtest ----------
@dataclass
class FoldResult:
    cutoff: pd.Timestamp
    forecasts: pd.DataFrame   # one row per store x family x date, actual + each model
    model: lgb.Booster


def run_fold(panel: pd.DataFrame, cutoff: str) -> FoldResult:
    cutoff = pd.Timestamp(cutoff)
    end = cutoff + pd.Timedelta(days=HORIZON)
    hist = panel[panel.date <= cutoff]
    future = panel[(panel.date > cutoff) & (panel.date <= end)].copy()

    model = fit_lgb(hist)
    fc = future[["date", "store_nbr", "family", "dow", "onpromotion", "sales"]].rename(columns={"sales": "actual"})
    fc["seasonal_naive"] = seasonal_naive(hist, future)
    fc["weekday_mean_4w"] = weekday_mean_4w(hist, future)
    fc["lightgbm"] = predict_lgb(model, future)

    dead = _dead_series(hist)
    for col in ["seasonal_naive", "weekday_mean_4w", "lightgbm"]:
        fc = _zero_dead(fc, dead, col)
    fc["horizon_day"] = (fc.date - cutoff).dt.days
    return FoldResult(cutoff, fc.reset_index(drop=True), model)


MODELS = ["seasonal_naive", "weekday_mean_4w", "lightgbm"]


def summarise(results: list[FoldResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        for m in MODELS:
            rows.append({"cutoff": r.cutoff.date(), "model": m, **score(r.forecasts.actual, r.forecasts[m])})
    return pd.DataFrame(rows)
