-- Daily chain sales with a 28-day centred moving average, plus store-traffic (transactions).
SELECT d.date,
       d.sales,
       AVG(d.sales) OVER (ORDER BY d.date ROWS BETWEEN 13 PRECEDING AND 14 FOLLOWING) AS sales_ma28,
       d.open_stores,
       t.transactions
FROM daily_totals d
LEFT JOIN (SELECT date, SUM(transactions) AS transactions FROM transactions GROUP BY date) t USING (date)
ORDER BY d.date;
