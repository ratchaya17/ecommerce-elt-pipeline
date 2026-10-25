-- Dimension: Customers
CREATE OR REPLACE TABLE dim_customers AS
SELECT
    ROW_NUMBER() OVER (ORDER BY customer_id) AS customer_key,
    customer_id,
    first_name || ' ' || last_name AS full_name,
    email,
    city,
    signup_date,
    'Q' || CAST(EXTRACT(QUARTER FROM signup_date) AS VARCHAR) || '-' || CAST(EXTRACT(YEAR FROM signup_date) AS VARCHAR) AS signup_cohort
FROM stg_customers;

-- Dimension: Products
CREATE OR REPLACE TABLE dim_products AS
SELECT
    ROW_NUMBER() OVER (ORDER BY product_id) AS product_key,
    product_id,
    product_name,
    category,
    price AS unit_price,
    CASE 
        WHEN price < 1000 THEN 'Budget (< 1000)'
        WHEN price BETWEEN 1000 AND 3000 THEN 'Mid-Range (1000-3000)'
        ELSE 'Premium (> 3000)'
    END AS price_tier
FROM stg_products;

-- Dimension: Calendar Date
CREATE OR REPLACE TABLE dim_date AS
WITH date_series AS (
    SELECT CAST('2024-01-01' AS DATE) + INTERVAL (n) DAY AS calendar_date
    FROM range(0, 366) AS t(n)
)
SELECT
    CAST(STRFTIME(calendar_date, '%Y%m%d') AS INTEGER) AS date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date) AS year,
    EXTRACT(MONTH FROM calendar_date) AS month,
    STRFTIME(calendar_date, '%B') AS month_name,
    EXTRACT(QUARTER FROM calendar_date) AS quarter,
    STRFTIME(calendar_date, '%A') AS day_of_week,
    CASE WHEN EXTRACT(DOW FROM calendar_date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_series;

-- Central Fact: Orders
CREATE OR REPLACE TABLE fact_orders AS
SELECT
    ROW_NUMBER() OVER (ORDER BY o.order_id) AS order_key,
    o.order_id,
    c.customer_key,
    p.product_key,
    CAST(STRFTIME(o.order_date, '%Y%m%d') AS INTEGER) AS order_date_key,
    o.order_date,
    o.quantity,
    p.unit_price,
    CAST(o.quantity * p.unit_price AS DECIMAL(10, 2)) AS total_amount,
    o.status,
    CASE WHEN o.status = 'Completed' THEN 1 ELSE 0 END AS is_completed
FROM stg_orders o
INNER JOIN dim_customers c ON o.customer_id = c.customer_id
INNER JOIN dim_products p ON o.product_id = p.product_id;
