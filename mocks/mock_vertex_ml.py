import pandas as pd
from typing import Optional
from .mock_bigquery import MockBigQueryClient


class MockModel:
    def __init__(self, display_name: str, resource_name: str, metrics: dict):
        self.display_name = display_name
        self.resource_name = resource_name
        self.metrics = metrics


class MockVertexAI:
    def __init__(self, project: str = "mock-trail-project-1", region: str = "asia-south1"):
        self.project = project
        self.region = region
        self.bq_client = MockBigQueryClient(project=project)

    def prepare_training_data(self) -> pd.DataFrame:
        """Extracts features and target variable from Gold layer."""
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
            dim_customer[["customer_key", "state"]],
            on="customer_key",
            how="left"
        ).merge(
            dim_product[["product_key", "category"]],
            on="product_key",
            how="left"
        )

        merged["high_value_order"] = (merged["total_sales"] >= 10000).astype(int)
        
        training_df = merged[[
            "quantity", "unit_price", "state", "category", "payment_method", "high_value_order"
        ]].copy()

        self.bq_client.save_table("gold_ml_high_value_orders", training_df)
        print(f"[MOCK VERTEX AI] Created ML training table with {len(training_df)} records.")
        return training_df

    def train_automl_model(self) -> MockModel:
        """Simulates Vertex AI AutoML Tabular training job and returns trained model metadata."""
        df = self.prepare_training_data()
        
        print("\n--- [MOCK VERTEX AI] Starting AutoML Tabular Training Job ---")
        print(f"Dataset: high-value-orders-dataset ({len(df)} samples)")
        print("Target column: 'high_value_order'")
        print("Optimization objective: 'maximize-au-roc'")
        print("Budget: 1000 milli-node-hours")
        
        # Calculate distribution and evaluation metrics
        positive_rate = df["high_value_order"].mean()
        metrics = {
            "au_roc": 0.965,
            "log_loss": 0.182,
            "precision": 0.941,
            "recall": 0.923,
            "accuracy": 0.950,
            "positive_class_ratio": round(positive_rate, 3)
        }
        
        model_name = "high-value-order-classifier-v1"
        resource_name = f"projects/{self.project}/locations/{self.region}/models/mock-model-738910"
        
        print("[OK] AutoML training completed successfully.")
        print(f"[OK] Model Name: {model_name}")
        print(f"[OK] Model Resource: {resource_name}")
        print(f"[OK] Model Metrics: ROC-AUC={metrics['au_roc']}, Precision={metrics['precision']}, Recall={metrics['recall']}")
        print("--- [MOCK VERTEX AI] Model Registered in Vertex AI Registry ---\n")

        return MockModel(model_name, resource_name, metrics)
