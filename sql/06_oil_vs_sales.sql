-- Ecuador is an oil-exporting economy: monthly oil price vs. average daily sales per open store.
SELECT date_trunc('month', d.date)               AS month,
       ROUND(AVG(o.oil_price), 2)                AS oil_price,
       ROUND(AVG(d.sales / NULLIF(d.open_stores, 0)), 0) AS sales_per_open_store
FROM daily_totals d
LEFT JOIN oil o USING (date)
GROUP BY 1
HAVING COUNT(o.oil_price) > 0
ORDER BY 1;
