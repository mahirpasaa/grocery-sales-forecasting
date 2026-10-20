-- Base views over the Parquet files. {data} is replaced with the parquet folder path.
CREATE OR REPLACE VIEW sales        AS SELECT * FROM '{data}/sales.parquet';
CREATE OR REPLACE VIEW stores       AS SELECT * FROM '{data}/stores.parquet';
CREATE OR REPLACE VIEW oil          AS SELECT * FROM '{data}/oil.parquet';
CREATE OR REPLACE VIEW holidays     AS SELECT * FROM '{data}/holidays.parquet';
CREATE OR REPLACE VIEW transactions AS SELECT * FROM '{data}/transactions.parquet';

-- National days off actually observed (a 'transferred' holiday is celebrated on its 'Transfer' row instead).
CREATE OR REPLACE VIEW national_holidays AS
SELECT DISTINCT date, description, type
FROM holidays
WHERE locale = 'National'
  AND type IN ('Holiday', 'Transfer', 'Additional', 'Bridge')
  AND NOT transferred;

-- Chain-level daily totals.
CREATE OR REPLACE VIEW daily_totals AS
SELECT s.date,
       SUM(s.sales)                                   AS sales,
       COUNT(DISTINCT s.store_nbr) FILTER (s.sales > 0) AS open_stores,
       SUM(s.onpromotion)                             AS items_on_promo
FROM sales s
GROUP BY s.date;
