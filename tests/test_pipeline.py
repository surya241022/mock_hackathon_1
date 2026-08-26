import os
import unittest
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class TestPipelineDataIntegrity(unittest.TestCase):

    def test_customers_data_integrity(self):
        customers_path = os.path.join(DATA_DIR, "customers.csv")
        self.assertTrue(os.path.exists(customers_path), "customers.csv not found")
        df = pd.read_csv(customers_path)
        self.assertFalse(df.empty, "customers.csv is empty")
        required_cols = {"customer_id", "customer_name", "state", "signup_date"}
        self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in customers: {required_cols - set(df.columns)}")
        self.assertTrue(df["customer_id"].is_unique, "customer_id must be unique")

    def test_products_data_integrity(self):
        products_path = os.path.join(DATA_DIR, "products.csv")
        self.assertTrue(os.path.exists(products_path), "products.csv not found")
        df = pd.read_csv(products_path)
        self.assertFalse(df.empty, "products.csv is empty")
        required_cols = {"product_id", "product_name", "category", "unit_price", "stock_quantity"}
        self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in products: {required_cols - set(df.columns)}")
        self.assertTrue((df["unit_price"] > 0).all(), "Unit price must be greater than zero")

    def test_orders_data_integrity(self):
        orders_path = os.path.join(DATA_DIR, "orders.csv")
        self.assertTrue(os.path.exists(orders_path), "orders.csv not found")
        df = pd.read_csv(orders_path)
        self.assertFalse(df.empty, "orders.csv is empty")
        required_cols = {"order_id", "order_date", "customer_id", "product_id", "quantity", "status", "payment_method"}
        self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in orders: {required_cols - set(df.columns)}")
        self.assertTrue((df["quantity"] > 0).all(), "Quantity must be greater than 0")

    def test_daily_sales_summary_data_integrity(self):
        summary_path = os.path.join(DATA_DIR, "daily_sales_summary.csv")
        self.assertTrue(os.path.exists(summary_path), "daily_sales_summary.csv not found")
        df = pd.read_csv(summary_path)
        self.assertFalse(df.empty, "daily_sales_summary.csv is empty")
        required_cols = {"order_date", "state", "total_orders", "total_units", "total_sales"}
        self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in summary: {required_cols - set(df.columns)}")


if __name__ == "__main__":
    unittest.main()
