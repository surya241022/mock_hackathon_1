from .mock_bigquery import MockBigQueryClient


def run_mock_airflow_pipeline(bq_client: MockBigQueryClient = None) -> dict:
    """Executes the validation tasks of the Airflow sales_pipeline_dag."""
    if bq_client is None:
        bq_client = MockBigQueryClient()

    print("\n--- [MOCK AIRFLOW] Executing sales_pipeline_dag ---")
    
    # Task 1: validate_gold
    print(">> [Task 1/2] Executing 'validate_gold'...")
    fact_sales = bq_client.get_table_df("gold_fact_sales")
    fact_count = len(fact_sales)
    print(f"[OK] Task 'validate_gold' SUCCESS: Found {fact_count} rows in gold.fact_sales.")

    # Task 2: validate_dimensions
    print(">> [Task 2/2] Executing 'validate_dimensions'...")
    customer_count = len(bq_client.get_table_df("gold_dim_customer"))
    product_count = len(bq_client.get_table_df("gold_dim_product"))
    date_count = len(bq_client.get_table_df("gold_dim_date"))
    print("[OK] Task 'validate_dimensions' SUCCESS:")
    print(f"   - dim_customer: {customer_count} records")
    print(f"   - dim_product:  {product_count} records")
    print(f"   - dim_date:     {date_count} records")

    print("--- [MOCK AIRFLOW] DAG Run Status: SUCCESS ---\n")

    return {
        "status": "SUCCESS",
        "fact_sales_rows": fact_count,
        "dim_customer_rows": customer_count,
        "dim_product_rows": product_count,
        "dim_date_rows": date_count
    }
