import re
import math
from collections import Counter
from typing import List, Dict, Tuple
import pandas as pd
from .mock_bigquery import MockBigQueryClient


def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())


def cosine_sim(vec1: Counter, vec2: Counter) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([val ** 2 for val in vec1.values()])
    sum2 = sum([val ** 2 for val in vec2.values()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator


class MockRAGSystem:
    def __init__(self, project: str = "mock-trail-project-1"):
        self.project = project
        self.bq_client = MockBigQueryClient(project=project)
        self.documents: List[Dict[str, str]] = []

    def create_rag_documents_and_embeddings(self) -> int:
        """Emulates BigQuery AI.EMBED on gold layer data to create rag_documents and embeddings."""
        print("\n--- [MOCK RAG] Creating Documents & Embeddings ---")
        fact_sales = self.bq_client.get_table_df("gold_fact_sales")
        dim_customer = self.bq_client.get_table_df("gold_dim_customer")
        dim_product = self.bq_client.get_table_df("gold_dim_product")
        dim_date = self.bq_client.get_table_df("gold_dim_date")

        if fact_sales.empty:
            from .mock_dataform import run_mock_dataform_transformations
            run_mock_dataform_transformations(self.bq_client)
            fact_sales = self.bq_client.get_table_df("gold_fact_sales")
            dim_customer = self.bq_client.get_table_df("gold_dim_customer")
            dim_product = self.bq_client.get_table_df("gold_dim_product")
            dim_date = self.bq_client.get_table_df("gold_dim_date")

        merged = fact_sales.merge(
            dim_customer[["customer_key", "state", "customer_name"]],
            on="customer_key",
            how="left"
        ).merge(
            dim_product[["product_key", "product_name", "category"]],
            on="product_key",
            how="left"
        ).merge(
            dim_date[["date_key", "full_date"]],
            on="date_key",
            how="left"
        )

        docs = []
        for _, row in merged.iterrows():
            content = (
                f"Sales order {row['order_id']}. "
                f"Date: {row.get('full_date', 'N/A')}. "
                f"Customer: {row.get('customer_name', 'N/A')} from state: {row.get('state', 'N/A')}. "
                f"Product: {row.get('product_name', 'N/A')} (Category: {row.get('category', 'N/A')}). "
                f"Quantity: {row['quantity']}. Unit price: ${row['unit_price']:.2f}. "
                f"Total sales: ${row['total_sales']:.2f}. "
                f"Payment method: {row['payment_method']}. "
                f"Order status: {row['status']}."
            )
            docs.append({
                "record_id": str(row['order_id']),
                "content": content
            })

        self.documents = docs
        doc_df = pd.DataFrame(docs)
        self.bq_client.save_table("gold_rag_embeddings", doc_df)
        print(f"[OK] Generated AI.EMBED (gemini-embedding-001) for {len(docs)} sales records.")
        print("[OK] Created table: gold.rag_embeddings")
        print("--- [MOCK RAG] Embedding Generation Completed ---\n")
        return len(docs)

    def search_and_answer(self, question: str, top_k: int = 5) -> Tuple[List[Dict], str]:
        """Performs mock BigQuery VECTOR_SEARCH and synthesizes answer using Gemini."""
        if not self.documents:
            self.create_rag_documents_and_embeddings()

        q_vec = Counter(tokenize(question))
        scored_docs = []
        for doc in self.documents:
            d_vec = Counter(tokenize(doc["content"]))
            score = cosine_sim(q_vec, d_vec)
            scored_docs.append({
                "record_id": doc["record_id"],
                "content": doc["content"],
                "similarity": score,
                "distance": round(1.0 - score, 4)
            })

        # Rank by similarity
        ranked_docs = sorted(scored_docs, key=lambda x: x["similarity"], reverse=True)[:top_k]

        # Generate factual response based on retrieved documents
        matching_snippets = [d['content'] for d in ranked_docs if d['similarity'] > 0.05]
        if not matching_snippets:
            answer = "Based on the retrieved sales records, no directly matching order information was found for your query."
        else:
            answer = (
                f"Based on the top {len(matching_snippets)} retrieved sales records:\n\n"
                + "\n".join([f"- {s}" for s in matching_snippets[:3]]) +
                f"\n\nSummary: Found relevant transaction details addressing '{question}'."
            )

        return ranked_docs, answer
