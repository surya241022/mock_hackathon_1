import pandas as pd
from typing import Dict, Any
from .mock_bigquery import MockBigQueryClient


class MockSalesAgent:
    """Mock Sales Intelligence Agent powered by local BigQuery Gold layer."""

    def __init__(self, project: str = "mock-trail-project-1"):
        self.project = project
        self.bq_client = MockBigQueryClient(project=project)

    def answer_query(self, user_question: str) -> str:
        q_lower = user_question.lower()

        fact_sales = self.bq_client.get_table_df("gold_fact_sales")
        dim_customer = self.bq_client.get_table_df("gold_dim_customer")
        dim_product = self.bq_client.get_table_df("gold_dim_product")

        if fact_sales.empty:
            from .mock_dataform import run_mock_dataform_transformations
            run_mock_dataform_transformations(self.bq_client)
            fact_sales = self.bq_client.get_table_df("gold_fact_sales")
            dim_customer = self.bq_client.get_table_df("gold_dim_customer")
            dim_product = self.bq_client.get_table_df("gold_dim_product")

        merged = fact_sales.merge(
            dim_customer[["customer_key", "state", "customer_name"]],
            on="customer_key",
            how="left"
        ).merge(
            dim_product[["product_key", "product_name", "category"]],
            on="product_key",
            how="left"
        )

        completed = merged[merged["status"] == "Completed"] if "status" in merged.columns else merged

        total_sales = completed["total_sales"].sum() if not completed.empty else 0
        total_orders = completed["order_id"].nunique() if not completed.empty else 0
        total_units = completed["quantity"].sum() if not completed.empty else 0
        avg_order_val = total_sales / total_orders if total_orders > 0 else 0

        if "total sales" in q_lower or "revenue" in q_lower:
            return f"According to the Gold layer in BigQuery, the total completed sales revenue is ${total_sales:,.2f} across {total_orders} completed orders."

        elif "state" in q_lower or "region" in q_lower:
            state_summary = completed.groupby("state")["total_sales"].sum().sort_values(ascending=False)
            top_state = state_summary.index[0] if not state_summary.empty else "N/A"
            top_sales = state_summary.iloc[0] if not state_summary.empty else 0
            breakdown = ", ".join([f"{k}: ${v:,.2f}" for k, v in state_summary.items()])
            return f"State performance breakdown (Gold layer):\n{breakdown}\nTop performing state is {top_state} with ${top_sales:,.2f} in sales."

        elif "product" in q_lower or "category" in q_lower:
            cat_summary = completed.groupby("category")["total_sales"].sum().sort_values(ascending=False)
            top_cat = cat_summary.index[0] if not cat_summary.empty else "N/A"
            breakdown = ", ".join([f"{k}: ${v:,.2f}" for k, v in cat_summary.items()])
            return f"Category sales breakdown:\n{breakdown}\nTop performing category is {top_cat}."

        else:
            return (
                f"Sales Intelligence Summary (BigQuery Gold Layer):\n"
                f"- Total Sales Revenue: ${total_sales:,.2f}\n"
                f"- Total Completed Orders: {total_orders}\n"
                f"- Total Units Sold: {total_units}\n"
                f"- Average Order Value: ${avg_order_val:,.2f}"
            )
