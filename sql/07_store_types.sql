-- Store formats compared on 2016 performance: sales per store-day, traffic and average ticket.
WITH store_2016 AS (
    SELECT s.store_nbr,
           SUM(s.sales) / COUNT(DISTINCT s.date) AS sales_per_day
    FROM sales s
    WHERE year(s.date) = 2016
    GROUP BY s.store_nbr
),
tx_2016 AS (
    SELECT store_nbr, AVG(transactions) AS tx_per_day
    FROM transactions
    WHERE year(date) = 2016
    GROUP BY store_nbr
)
SELECT st.type                                    AS store_type,
       COUNT(*)                                   AS stores,
       ROUND(AVG(s.sales_per_day))                AS avg_sales_per_day,
       ROUND(AVG(t.tx_per_day))                   AS avg_transactions_per_day,
       ROUND(SUM(s.sales_per_day) / SUM(t.tx_per_day), 2) AS avg_ticket
FROM stores st
JOIN store_2016 s USING (store_nbr)
JOIN tx_2016    t USING (store_nbr)
GROUP BY st.type
ORDER BY avg_sales_per_day DESC;
