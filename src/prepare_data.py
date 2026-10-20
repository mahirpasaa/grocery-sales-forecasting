"""Convert the raw Favorita CSVs into typed Parquet files.

Usage:
    python src/prepare_data.py

Expects the Kaggle CSVs in ./data (see README). Writes ./data/parquet/*.parquet.
"""
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parents[1] / "data"
OUT = DATA / "parquet"

TABLES = {
    "sales": "SELECT CAST(date AS DATE) AS date, store_nbr, family, sales, onpromotion FROM read_csv_auto('{src}')",
    "stores": "SELECT * FROM read_csv_auto('{src}')",
    "oil": "SELECT CAST(date AS DATE) AS date, dcoilwtico AS oil_price FROM read_csv_auto('{src}')",
    "holidays": "SELECT CAST(date AS DATE) AS date, * EXCLUDE (date) FROM read_csv_auto('{src}')",
    "transactions": "SELECT CAST(date AS DATE) AS date, store_nbr, transactions FROM read_csv_auto('{src}')",
    "test": "SELECT CAST(date AS DATE) AS date, store_nbr, family, onpromotion FROM read_csv_auto('{src}')",
}
FILES = {"sales": "train.csv", "stores": "stores.csv", "oil": "oil.csv",
         "holidays": "holidays_events.csv", "transactions": "transactions.csv", "test": "test.csv"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for table, select in TABLES.items():
        src = DATA / FILES[table]
        if not src.exists():
            raise FileNotFoundError(f"Missing {src}. Download the dataset first (see README).")
        dst = OUT / f"{table}.parquet"
        con.execute(f"COPY ({select.format(src=src.as_posix())}) TO '{dst.as_posix()}' (FORMAT PARQUET)")
        rows = con.execute(f"SELECT COUNT(*) FROM '{dst.as_posix()}'").fetchone()[0]
        print(f"{table:<13} {rows:>10,} rows -> {dst.name}")


if __name__ == "__main__":
    main()
