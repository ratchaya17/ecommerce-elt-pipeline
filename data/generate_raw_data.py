"""
Raw Data Generator for E-Commerce ELT Pipeline
----------------------------------------------
This script generates realistic raw e-commerce data:
1. raw_customers.csv (Customer profile & location)
2. raw_products.csv (Product catalog & pricing)
3. raw_orders.csv (Order transactions)

Uses only Python's built-in libraries (csv, random, datetime).
"""

import csv
import random
from datetime import datetime, timedelta
import os

# Set seed for reproducible data
random.seed(42)

# Ensure output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_customers(num_customers=100):
    first_names = ["Aarav", "Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Rohan", "Pooja", "Karthik", "Divya", "Siddharth", "Meera", "Arjun", "Kavya", "Aditya"]
    last_names = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Kumar", "Singh", "Das", "Menon", "Pillai", "Gupta", "Joshi", "Chopra"]
    cities = ["Chennai", "Bangalore", "Hyderabad", "Mumbai", "Delhi", "Kolkata", "Pune", "Coimbatore"]
    
    customers = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(1, num_customers + 1):
        f_name = random.choice(first_names)
        l_name = random.choice(last_names)
        city = random.choice(cities)
        signup_offset = random.randint(0, 180) # Signed up within first 6 months of 2024
        signup_date = (base_date + timedelta(days=signup_offset)).strftime("%Y-%m-%d")
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "first_name": f_name,
            "last_name": l_name,
            "email": f"{f_name.lower()}.{l_name.lower()}{i}@example.com",
            "city": city,
            "signup_date": signup_date
        })
        
    filepath = os.path.join(OUTPUT_DIR, "raw_customers.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["customer_id", "first_name", "last_name", "email", "city", "signup_date"])
        writer.writeheader()
        writer.writerows(customers)
    print(f"[OK] Generated {len(customers)} customers -> {filepath}")
    return customers

def generate_products():
    catalog = [
        ("PROD_001", "Wireless Bluetooth Earbuds", "Electronics", 1999.00),
        ("PROD_002", "Mechanical Keyboard RGB", "Electronics", 3499.00),
        ("PROD_003", "Ergonomic Office Chair", "Furniture", 8999.00),
        ("PROD_004", "Stainless Steel Water Bottle", "Home & Kitchen", 649.00),
        ("PROD_005", "Running Shoes Pro 3", "Footwear", 2899.00),
        ("PROD_006", "Smart Fitness Band 6", "Electronics", 2499.00),
        ("PROD_007", "Cotton Polo T-Shirt", "Apparel", 799.00),
        ("PROD_008", "Ceramic Coffee Mug Set", "Home & Kitchen", 499.00),
        ("PROD_009", "Laptop Backpack 30L", "Accessories", 1499.00),
        ("PROD_010", "Noise Cancelling Headphones", "Electronics", 5999.00),
        ("PROD_011", "Denim Slim Fit Jeans", "Apparel", 1699.00),
        ("PROD_012", "Yoga Mat Non-Slip 6mm", "Fitness", 899.00),
    ]
    
    filepath = os.path.join(OUTPUT_DIR, "raw_products.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_name", "category", "price"])
        writer.writerows(catalog)
    print(f"[OK] Generated {len(catalog)} products -> {filepath}")
    return [p[0] for p in catalog]

def generate_orders(customers, product_ids, num_orders=600):
    orders = []
    base_date = datetime(2024, 1, 15)
    statuses = ["Completed", "Completed", "Completed", "Completed", "Returned", "Cancelled"]
    
    cust_ids = [c["customer_id"] for c in customers]
    
    for i in range(1, num_orders + 1):
        order_offset = random.randint(0, 320) # Spread across 2024
        order_date = (base_date + timedelta(days=order_offset)).strftime("%Y-%m-%d")
        
        orders.append({
            "order_id": f"ORD_{i:05d}",
            "customer_id": random.choice(cust_ids),
            "product_id": random.choice(product_ids),
            "order_date": order_date,
            "quantity": random.choices([1, 2, 3, 4, 5], weights=[60, 25, 10, 3, 2])[0],
            "status": random.choice(statuses)
        })
        
    filepath = os.path.join(OUTPUT_DIR, "raw_orders.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "customer_id", "product_id", "order_date", "quantity", "status"])
        writer.writeheader()
        writer.writerows(orders)
    print(f"[OK] Generated {len(orders)} orders -> {filepath}")

if __name__ == "__main__":
    print("[INFO] Generating raw E-Commerce datasets...")
    custs = generate_customers(num_customers=100)
    prods = generate_products()
    generate_orders(custs, prods, num_orders=600)
    print("[SUCCESS] All raw datasets created successfully!")
