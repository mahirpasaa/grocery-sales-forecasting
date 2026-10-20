-- Effect of each national holiday: sales on the day vs. the average of the same weekday
-- in the 3 weeks before and after (excluding other holidays).
WITH h AS (
    SELECT date, ANY_VALUE(description) AS description
    FROM national_holidays
    WHERE date BETWEEN DATE '2013-02-01' AND DATE '2017-07-15'
    GROUP BY date
),
ref AS (
    SELECT h.date,
           AVG(d.sales) AS ref_sales
    FROM h
    JOIN daily_totals d
      ON d.date IN (h.date - 21, h.date - 14, h.date - 7, h.date + 7, h.date + 14, h.date + 21)
    WHERE d.date NOT IN (SELECT date FROM national_holidays)
    GROUP BY h.date
)
SELECT h.date,
       h.description,
       ROUND((d.sales / r.ref_sales - 1) * 100, 1) AS effect_pct
FROM h
JOIN daily_totals d USING (date)
JOIN ref r USING (date)
ORDER BY h.date;
