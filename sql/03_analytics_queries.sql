-- 1. Top 3 spending customers per city
WITH customer_spending AS (
    SELECT
        c.city,
        c.full_name,
        c.email,
        ROUND(SUM(f.total_amount), 2) AS total_spent,
        COUNT(f.order_id) AS total_orders
    FROM fact_orders f
    INNER JOIN dim_customers c ON f.customer_key = c.customer_key
    WHERE f.is_completed = 1
    GROUP BY c.city, c.full_name, c.email
),
ranked_customers AS (
    SELECT
        city,
        full_name,
        email,
        total_spent,
        total_orders,
        DENSE_RANK() OVER (
            PARTITION BY city 
            ORDER BY total_spent DESC
        ) AS rank_in_city
    FROM customer_spending
)
SELECT
    city,
    rank_in_city,
    full_name,
    total_spent,
    total_orders
FROM ranked_customers
WHERE rank_in_city <= 3
ORDER BY city, rank_in_city;


-- 2. Month-over-Month (MoM) revenue growth
WITH monthly_revenue AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        ROUND(SUM(f.total_amount), 2) AS current_month_revenue,
        COUNT(f.order_id) AS total_orders
    FROM fact_orders f
    INNER JOIN dim_date d ON f.order_date_key = d.date_key
    WHERE f.is_completed = 1
    GROUP BY d.year, d.month, d.month_name
),
revenue_with_lag AS (
    SELECT
        year,
        month,
        month_name,
        current_month_revenue,
        LAG(current_month_revenue, 1) OVER (ORDER BY year, month) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT
    year,
    month_name,
    current_month_revenue,
    COALESCE(prev_month_revenue, 0) AS prev_month_revenue,
    ROUND(current_month_revenue - COALESCE(prev_month_revenue, current_month_revenue), 2) AS revenue_change,
    ROUND(
        ((current_month_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0)) * 100, 
        2
    ) AS mom_growth_percentage
FROM revenue_with_lag
ORDER BY year, month;


-- 3. Average days between repeat orders
WITH order_sequence AS (
    SELECT
        c.customer_id,
        c.full_name,
        f.order_id,
        f.order_date,
        LEAD(f.order_date, 1) OVER (
            PARTITION BY c.customer_id 
            ORDER BY f.order_date
        ) AS next_order_date
    FROM fact_orders f
    INNER JOIN dim_customers c ON f.customer_key = c.customer_key
    WHERE f.is_completed = 1
),
order_diffs AS (
    SELECT
        customer_id,
        full_name,
        order_id,
        order_date,
        next_order_date,
        (next_order_date - order_date) AS days_until_next_order
    FROM order_sequence
    WHERE next_order_date IS NOT NULL
)
SELECT
    customer_id,
    full_name,
    COUNT(*) AS repeat_purchases,
    ROUND(AVG(days_until_next_order), 1) AS avg_days_between_orders,
    MIN(days_until_next_order) AS quickest_repeat_days,
    MAX(days_until_next_order) AS longest_gap_days
FROM order_diffs
GROUP BY customer_id, full_name
HAVING COUNT(*) >= 2
ORDER BY avg_days_between_orders ASC
LIMIT 10;


-- 4. Cumulative running sales
WITH daily_revenue AS (
    SELECT
        order_date,
        ROUND(SUM(total_amount), 2) AS daily_sales
    FROM fact_orders
    WHERE is_completed = 1
    GROUP BY order_date
)
SELECT
    order_date,
    daily_sales,
    ROUND(SUM(daily_sales) OVER (ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue
FROM daily_revenue
ORDER BY order_date
LIMIT 15;


-- 5. Return and cancellation rates by product category
WITH category_metrics AS (
    SELECT
        p.category,
        COUNT(f.order_id) AS total_orders,
        SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END) AS completed_orders,
        SUM(CASE WHEN f.status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders,
        SUM(CASE WHEN f.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
        ROUND(SUM(CASE WHEN f.status = 'Completed' THEN f.total_amount ELSE 0 END), 2) AS net_revenue
    FROM fact_orders f
    INNER JOIN dim_products p ON f.product_key = p.product_key
    GROUP BY p.category
)
SELECT
    category,
    total_orders,
    completed_orders,
    returned_orders,
    ROUND((returned_orders * 100.0) / total_orders, 2) AS return_rate_pct,
    net_revenue,
    ROUND((net_revenue * 100.0) / SUM(net_revenue) OVER (), 2) AS revenue_share_pct
FROM category_metrics
ORDER BY net_revenue DESC;
