"""Tiny helper that runs the queries in ./sql against DuckDB and returns DataFrames."""
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
PARQUET_DIR = ROOT / "data" / "parquet"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    run_script(con, "00_views.sql")
    return con


def _render(name: str, **params) -> str:
    sql = (SQL_DIR / name).read_text(encoding="utf-8")
    params.setdefault("data", PARQUET_DIR.as_posix())
    for key, value in params.items():
        sql = sql.replace("{" + key + "}", str(value))
    return sql


def run_script(con: duckdb.DuckDBPyConnection, name: str, **params) -> None:
    con.execute(_render(name, **params))


def query(con: duckdb.DuckDBPyConnection, name: str, **params) -> pd.DataFrame:
    return con.execute(_render(name, **params)).df()
