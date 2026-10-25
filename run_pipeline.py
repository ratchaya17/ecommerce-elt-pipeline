"""
E-Commerce ELT Pipeline Runner & Analytics Engine
-------------------------------------------------
Orchestrates the end-to-end data pipeline:
1. Connects to embedded DuckDB database (ecommerce_warehouse.duckdb)
2. Runs 01_staging.sql (Ingestion & Type Casting)
3. Runs 02_dimensional_model.sql (Kimball Star Schema creation)
4. Executes and displays key business analytical queries
5. Exports dimensional marts to columnar Parquet files
"""

import duckdb
import os
import sys
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Always set current working directory to project directory for reliable relative paths
os.chdir(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "ecommerce_warehouse.duckdb")
SQL_DIR = os.path.join(BASE_DIR, "sql")
MART_DIR = os.path.join(BASE_DIR, "data", "mart")
os.makedirs(MART_DIR, exist_ok=True)

def execute_sql_file(con, filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    con.execute(sql)

def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_pipeline():
    start_time = time.time()
    print_separator("STARTING E-COMMERCE ELT PIPELINE")
    
    # 1. Connect to DuckDB database file
    print(f"[INFO] Initializing DuckDB warehouse: {DB_PATH}")
    con = duckdb.connect(DB_PATH)
    
    # 2. Execute Staging Layer
    staging_file = os.path.join(SQL_DIR, "01_staging.sql")
    print(f"[STAGE 1] Ingesting CSVs to Staging Tables from: {staging_file} ...")
    execute_sql_file(con, staging_file)
    print("   -> Staging tables created: stg_customers, stg_products, stg_orders")
    
    # 3. Execute Dimensional Modeling Layer (Star Schema)
    dim_file = os.path.join(SQL_DIR, "02_dimensional_model.sql")
    print(f"[STAGE 2] Building Kimball Star Schema from: {dim_file} ...")
    execute_sql_file(con, dim_file)
    print("   -> Dimension tables created: dim_customers, dim_products, dim_date")
    print("   -> Fact table created:       fact_orders")

    # 4. Display Warehouse Summary
    print_separator("WAREHOUSE SCHEMA SUMMARY")
    counts = con.execute("""
        SELECT 'dim_customers' AS table_name, count(*) AS row_count FROM dim_customers
        UNION ALL
        SELECT 'dim_products', count(*) FROM dim_products
        UNION ALL
        SELECT 'dim_date', count(*) FROM dim_date
        UNION ALL
        SELECT 'fact_orders', count(*) FROM fact_orders
    """).fetchall()
    for table_name, count in counts:
        print(f"   * {table_name:<18} : {count:>5} rows")

    # 5. Execute Business Insights
    print_separator("ANALYTICS 1: TOP 2 SPENDING CUSTOMERS PER CITY (RANK + CTE)")
    con.sql("""
        WITH customer_spending AS (
            SELECT
                c.city,
                c.full_name,
                ROUND(SUM(f.total_amount), 2) AS total_spent,
                COUNT(f.order_id) AS total_orders
            FROM fact_orders f
            INNER JOIN dim_customers c ON f.customer_key = c.customer_key
            WHERE f.is_completed = 1
            GROUP BY c.city, c.full_name
        ),
        ranked AS (
            SELECT
                city,
                full_name,
                total_spent,
                total_orders,
                DENSE_RANK() OVER (PARTITION BY city ORDER BY total_spent DESC) AS city_rank
            FROM customer_spending
        )
        SELECT city, city_rank, full_name, total_spent, total_orders
        FROM ranked
        WHERE city_rank <= 2
        ORDER BY city, city_rank
        LIMIT 10;
    """).show()

    print_separator("ANALYTICS 2: MONTH-OVER-MONTH REVENUE GROWTH (LAG)")
    con.sql("""
        WITH monthly AS (
            SELECT
                d.year,
                d.month,
                d.month_name,
                ROUND(SUM(f.total_amount), 2) AS revenue
            FROM fact_orders f
            INNER JOIN dim_date d ON f.order_date_key = d.date_key
            WHERE f.is_completed = 1
            GROUP BY d.year, d.month, d.month_name
        ),
        with_lag AS (
            SELECT
                year,
                month,
                month_name,
                revenue,
                LAG(revenue, 1) OVER (ORDER BY year, month) AS prev_revenue
            FROM monthly
        )
        SELECT
            month_name,
            revenue AS current_rev_inr,
            COALESCE(prev_revenue, 0) AS prev_rev_inr,
            ROUND(((revenue - prev_revenue) / NULLIF(prev_revenue, 0)) * 100, 2) AS mom_growth_pct
        FROM with_lag
        ORDER BY year, month;
    """).show()

    print_separator("ANALYTICS 3: REPEAT PURCHASE FREQUENCY (LEAD)")
    con.sql("""
        WITH order_sequence AS (
            SELECT
                c.customer_id,
                c.full_name,
                f.order_date,
                LEAD(f.order_date, 1) OVER (PARTITION BY c.customer_id ORDER BY f.order_date) AS next_order_date
            FROM fact_orders f
            INNER JOIN dim_customers c ON f.customer_key = c.customer_key
            WHERE f.is_completed = 1
        ),
        gaps AS (
            SELECT
                customer_id,
                full_name,
                (next_order_date - order_date) AS days_gap
            FROM order_sequence
            WHERE next_order_date IS NOT NULL
        )
        SELECT
            full_name,
            COUNT(*) AS repeat_orders_count,
            ROUND(AVG(days_gap), 1) AS avg_days_between_orders
        FROM gaps
        GROUP BY customer_id, full_name
        HAVING COUNT(*) >= 2
        ORDER BY avg_days_between_orders ASC
        LIMIT 6;
    """).show()

    # 6. Export to Parquet (Gold Standard in Data Lake / Warehouse)
    print_separator("EXPORTING TO COLUMNAR PARQUET FORMAT")
    con.execute(f"COPY dim_customers TO '{os.path.join(MART_DIR, 'dim_customers.parquet')}' (FORMAT PARQUET);")
    con.execute(f"COPY dim_products TO '{os.path.join(MART_DIR, 'dim_products.parquet')}' (FORMAT PARQUET);")
    con.execute(f"COPY fact_orders TO '{os.path.join(MART_DIR, 'fact_orders.parquet')}' (FORMAT PARQUET);")
    print(f"[SUCCESS] Exported Parquet files to: {MART_DIR}")
    for fname in os.listdir(MART_DIR):
        fpath = os.path.join(MART_DIR, fname)
        print(f"   * {fname} ({os.path.getsize(fpath)} bytes)")

    con.close()
    elapsed = time.time() - start_time
    print_separator(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")

if __name__ == "__main__":
    run_pipeline()
