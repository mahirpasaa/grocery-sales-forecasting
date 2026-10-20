-- Promotion uplift per product family.
-- To limit confounding by store size and season, promo days are compared with non-promo days
-- of the SAME store x family x month, then the median uplift across those cells is taken.
-- (Observational, not a controlled test: promotions may be timed for high-demand periods.)
WITH cells AS (
    SELECT store_nbr,
           family,
           date_trunc('month', date)                       AS month,
           AVG(sales) FILTER (onpromotion > 0)             AS avg_promo,
           AVG(sales) FILTER (onpromotion = 0)             AS avg_no_promo,
           COUNT(*)   FILTER (onpromotion > 0)             AS promo_days,
           COUNT(*)   FILTER (onpromotion = 0)             AS no_promo_days
    FROM sales
    WHERE date >= DATE '2016-01-01'
    GROUP BY ALL
)
SELECT family,
       COUNT(*)                                                 AS comparable_cells,
       ROUND(MEDIAN(avg_promo / avg_no_promo - 1) * 100, 1)     AS median_uplift_pct
FROM cells
WHERE promo_days >= 3 AND no_promo_days >= 3 AND avg_no_promo > 0
GROUP BY family
HAVING COUNT(*) >= 30
ORDER BY median_uplift_pct DESC;
