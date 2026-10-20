-- Product-family contribution, growth and promotion intensity.
WITH by_year AS (
    SELECT family,
           SUM(sales) FILTER (year(date) = 2015) AS sales_2015,
           SUM(sales) FILTER (year(date) = 2016) AS sales_2016,
           SUM(sales)                            AS sales_total,
           AVG(CASE WHEN onpromotion > 0 THEN 1.0 ELSE 0 END) FILTER (date >= DATE '2016-01-01') AS promo_day_share,
           AVG(CASE WHEN sales = 0 THEN 1.0 ELSE 0 END)                                         AS zero_sales_share
    FROM sales
    GROUP BY family
)
SELECT family,
       ROUND(sales_total * 100.0 / SUM(sales_total) OVER (), 2)   AS sales_share_pct,
       ROUND((sales_2016 / NULLIF(sales_2015, 0) - 1) * 100, 1)   AS growth_2016_pct,
       ROUND(promo_day_share * 100, 1)                            AS promo_day_share_pct,
       ROUND(zero_sales_share * 100, 1)                           AS zero_sales_day_pct
FROM by_year
ORDER BY sales_share_pct DESC;
