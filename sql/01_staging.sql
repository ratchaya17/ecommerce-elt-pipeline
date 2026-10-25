-- 1. Customers Staging
CREATE OR REPLACE TABLE stg_customers AS
SELECT
    TRIM(customer_id) AS customer_id,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    LOWER(TRIM(email)) AS email,
    TRIM(city) AS city,
    CAST(signup_date AS DATE) AS signup_date
FROM read_csv_auto('data/raw/raw_customers.csv');

-- 2. Products Staging
CREATE OR REPLACE TABLE stg_products AS
SELECT
    TRIM(product_id) AS product_id,
    TRIM(product_name) AS product_name,
    TRIM(category) AS category,
    CAST(price AS DECIMAL(10, 2)) AS price
FROM read_csv_auto('data/raw/raw_products.csv');

-- 3. Orders Staging
CREATE OR REPLACE TABLE stg_orders AS
SELECT
    TRIM(order_id) AS order_id,
    TRIM(customer_id) AS customer_id,
    TRIM(product_id) AS product_id,
    CAST(order_date AS DATE) AS order_date,
    CAST(quantity AS INTEGER) AS quantity,
    TRIM(status) AS status
FROM read_csv_auto('data/raw/raw_orders.csv');
