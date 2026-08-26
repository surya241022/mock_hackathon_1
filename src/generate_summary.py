import pandas as pd
from pathlib import Path

# -----------------------------------------
# 1. Define data folder
# -----------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Input files
customers_file = DATA_DIR / "customers.csv"
products_file = DATA_DIR / "products.csv"
orders_file = DATA_DIR / "orders.csv"

# Output file
output_file = DATA_DIR / "daily_sales_summary.csv"


# -----------------------------------------
# 2. Read the three input CSV files
# -----------------------------------------
customers = pd.read_csv(customers_file)
products = pd.read_csv(products_file)
orders = pd.read_csv(orders_file)


# -----------------------------------------
# 3. Join orders with customer information
# -----------------------------------------
merged_data = orders.merge(
    customers,
    on="customer_id",
    how="left"
)


# -----------------------------------------
# 4. Join with product information
# -----------------------------------------
merged_data = merged_data.merge(
    products,
    on="product_id",
    how="left"
)


# -----------------------------------------
# 5. Keep only completed orders
# -----------------------------------------
completed_orders = merged_data[
    merged_data["status"] == "Completed"
].copy()


# -----------------------------------------
# 6. Calculate sales amount
# -----------------------------------------
completed_orders["sales_amount"] = (
    completed_orders["quantity"]
    * completed_orders["unit_price"]
)


# -----------------------------------------
# 7. Generate daily sales summary
# -----------------------------------------
daily_summary = (
    completed_orders
    .groupby(
        ["order_date", "state"],
        as_index=False
    )
    .agg(
        total_orders=("order_id", "nunique"),
        total_units=("quantity", "sum"),
        total_sales=("sales_amount", "sum")
    )
)


# -----------------------------------------
# 8. Sort the final data
# -----------------------------------------
daily_summary = daily_summary.sort_values(
    by=["order_date", "state"]
)


# -----------------------------------------
# 9. Save generated CSV
# -----------------------------------------
daily_summary.to_csv(
    output_file,
    index=False
)


# -----------------------------------------
# 10. Confirmation
# -----------------------------------------
print("Daily sales summary generated successfully!")
print(f"Saved to: {output_file}")
print(f"Rows generated: {len(daily_summary)}")