import zlib
import pandas as pd
from pathlib import Path
from .mock_bigquery import MockBigQueryClient


def farm_fingerprint(val: str) -> int:
    """Deterministic hash emulation for FARM_FINGERPRINT."""
    return zlib.crc32(str(val).encode('utf-8'))


def run_mock_dataform_transformations(bq_client: MockBigQueryClient = None):
    """Executes the Dataform Bronze -> Silver -> Gold transformations locally."""
    if bq_client is None:
        bq_client = MockBigQueryClient()

    print("\n--- [MOCK DATAFORM] Starting Silver & Gold Pipeline ---")

    # -------------------------------------------------------------
    # 1. Read Bronze Tables
    # -------------------------------------------------------------
    customers_raw = bq_client.get_table_df("bronze_customers_raw")
    products_raw = bq_client.get_table_df("bronze_products_raw")
    orders_raw = bq_client.get_table_df("bronze_orders_raw")
    daily_sales_raw = bq_client.get_table_df("bronze_daily_sales_summary_raw")

    # Fallback to reading data folder if bronze is empty
    data_dir = Path(__file__).resolve().parent.parent / "data"
    if customers_raw.empty and (data_dir / "customers.csv").exists():
        customers_raw = pd.read_csv(data_dir / "customers.csv")
    if products_raw.empty and (data_dir / "products.csv").exists():
        products_raw = pd.read_csv(data_dir / "products.csv")
    if orders_raw.empty and (data_dir / "orders.csv").exists():
        orders_raw = pd.read_csv(data_dir / "orders.csv")
    if daily_sales_raw.empty and (data_dir / "daily_sales_summary.csv").exists():
        daily_sales_raw = pd.read_csv(data_dir / "daily_sales_summary.csv")

    # -------------------------------------------------------------
    # 2. Build Silver Layer
    # -------------------------------------------------------------
    # silver.customers
    silver_customers = customers_raw.dropna(subset=["customer_id"]).copy()
    silver_customers["customer_id"] = silver_customers["customer_id"].astype(int)
    silver_customers["customer_name"] = silver_customers["customer_name"].str.strip()
    silver_customers["state"] = silver_customers["state"].str.strip()
    silver_customers["signup_date"] = pd.to_datetime(silver_customers["signup_date"]).dt.date
    bq_client.save_table("silver_customers", silver_customers)
    print(f"[OK] Created table: silver.customers ({len(silver_customers)} rows)")

    # silver.products
    silver_products = products_raw.dropna(subset=["product_id"]).copy()
    silver_products["product_id"] = silver_products["product_id"].astype(int)
    silver_products["product_name"] = silver_products["product_name"].str.strip()
    silver_products["category"] = silver_products["category"].str.strip()
    silver_products["unit_price"] = silver_products["unit_price"].astype(float)
    silver_products["stock_quantity"] = silver_products["stock_quantity"].astype(int)
    bq_client.save_table("silver_products", silver_products)
    print(f"[OK] Created table: silver.products ({len(silver_products)} rows)")

    # silver.orders
    silver_orders = orders_raw.dropna(subset=["order_id", "customer_id", "product_id"]).copy()
    silver_orders["order_id"] = silver_orders["order_id"].astype(int)
    silver_orders["order_date"] = pd.to_datetime(silver_orders["order_date"]).dt.date
    silver_orders["customer_id"] = silver_orders["customer_id"].astype(int)
    silver_orders["product_id"] = silver_orders["product_id"].astype(int)
    silver_orders["quantity"] = silver_orders["quantity"].astype(int)
    silver_orders["status"] = silver_orders["status"].str.strip()
    silver_orders["payment_method"] = silver_orders["payment_method"].str.strip()
    bq_client.save_table("silver_orders", silver_orders)
    print(f"[OK] Created table: silver.orders ({len(silver_orders)} rows)")

    # silver.sales_enriched
    sales_enriched = silver_orders.merge(
        silver_customers[["customer_id", "customer_name", "state", "signup_date"]].rename(columns={"state": "customer_state"}),
        on="customer_id",
        how="left"
    ).merge(
        silver_products[["product_id", "product_name", "category", "unit_price"]],
        on="product_id",
        how="left"
    )
    sales_enriched["total_sales"] = sales_enriched["quantity"] * sales_enriched["unit_price"]
    bq_client.save_table("silver_sales_enriched", sales_enriched)
    print(f"[OK] Created table: silver.sales_enriched ({len(sales_enriched)} rows)")

    # silver.daily_sales_summary
    if not daily_sales_raw.empty:
        silver_summary = daily_sales_raw.dropna(subset=["order_date", "state"]).copy()
        bq_client.save_table("silver_daily_sales_summary", silver_summary)
        print(f"[OK] Created table: silver.daily_sales_summary ({len(silver_summary)} rows)")

    # -------------------------------------------------------------
    # 3. Build Gold Layer (Star Schema)
    # -------------------------------------------------------------
    # gold.dim_customer
    dim_customer = silver_customers.copy()
    dim_customer["customer_key"] = dim_customer["customer_id"].apply(farm_fingerprint)
    bq_client.save_table("gold_dim_customer", dim_customer)
    print(f"[OK] Created table: gold.dim_customer ({len(dim_customer)} rows)")

    # gold.dim_product
    dim_product = silver_products.copy()
    dim_product["product_key"] = dim_product["product_id"].apply(farm_fingerprint)
    bq_client.save_table("gold_dim_product", dim_product)
    print(f"[OK] Created table: gold.dim_product ({len(dim_product)} rows)")

    # gold.dim_date
    min_date = sales_enriched["order_date"].min()
    max_date = sales_enriched["order_date"].max()
    dates = pd.date_range(start=min_date, end=max_date)
    dim_date = pd.DataFrame({
        "full_date": dates.date,
        "date_key": dates.strftime('%Y%m%d').astype(int),
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime('%B'),
        "week_of_year": dates.isocalendar().week.astype(int),
        "day_of_month": dates.day,
        "day_of_week": dates.dayofweek + 1,
        "day_name": dates.strftime('%A')
    })
    bq_client.save_table("gold_dim_date", dim_date)
    print(f"[OK] Created table: gold.dim_date ({len(dim_date)} rows)")

    # gold.fact_sales
    fact_sales = sales_enriched.copy()
    fact_sales["customer_key"] = fact_sales["customer_id"].apply(farm_fingerprint)
    fact_sales["product_key"] = fact_sales["product_id"].apply(farm_fingerprint)
    fact_sales["date_key"] = pd.to_datetime(fact_sales["order_date"]).dt.strftime('%Y%m%d').astype(int)
    
    fact_sales_cols = [
        "order_id", "date_key", "customer_key", "product_key",
        "quantity", "unit_price", "total_sales", "status", "payment_method"
    ]
    fact_sales_final = fact_sales[fact_sales_cols]
    bq_client.save_table("gold_fact_sales", fact_sales_final)
    print(f"[OK] Created table: gold.fact_sales ({len(fact_sales_final)} rows)")

    print("--- [MOCK DATAFORM] Transformations Completed Successfully ---\n")
    return fact_sales_final
