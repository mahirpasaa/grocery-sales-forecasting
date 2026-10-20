-- Sales index by day of week and by day of month (1.00 = average day), 2015-01-01 onwards,
-- excluding national holidays and the first days of January so they do not distort the profile.
-- Each day is indexed against its own month's average to remove trend and yearly seasonality.
WITH base AS (
    SELECT d.date,
           d.sales / AVG(d.sales) OVER (PARTITION BY date_trunc('month', d.date)) AS idx
    FROM daily_totals d
    WHERE d.date >= DATE '2015-01-01'
      AND d.date NOT IN (SELECT date FROM national_holidays)
      AND NOT (month(d.date) = 1 AND day(d.date) <= 2)
)
SELECT 'day_of_week'           AS dimension,
       isodow(date)            AS key,        -- 1 = Monday ... 7 = Sunday
       ROUND(AVG(idx), 3)      AS sales_index
FROM base GROUP BY 2
UNION ALL
SELECT 'day_of_month', day(date), ROUND(AVG(idx), 3)
FROM base GROUP BY 2
ORDER BY dimension, key;
