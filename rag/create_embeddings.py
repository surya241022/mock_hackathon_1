from google.cloud import bigquery


PROJECT_ID = "mock-trail-project-1"
DATASET = "gold"

client = bigquery.Client(project=PROJECT_ID)


# ---------------------------------------------------------
# STEP 1: Create a text representation of the Gold data
# ---------------------------------------------------------

create_documents_sql = f"""
CREATE OR REPLACE TABLE
`{PROJECT_ID}.{DATASET}.rag_documents` AS

SELECT
    CAST(f.order_id AS STRING) AS record_id,

    CONCAT(
        'Sales order ',
        CAST(f.order_id AS STRING),
        '. ',

        'Date: ',
        CAST(d.full_date AS STRING),
        '. ',

        'Customer state: ',
        c.state,
        '. ',

        'Product: ',
        p.product_name,
        '. ',

        'Category: ',
        p.category,
        '. ',

        'Quantity: ',
        CAST(f.quantity AS STRING),
        '. ',

        'Unit price: ',
        CAST(f.unit_price AS STRING),
        '. ',

        'Total sales: ',
        CAST(f.total_sales AS STRING),
        '. ',

        'Payment method: ',
        f.payment_method,
        '. ',

        'Order status: ',
        f.status,
        '.'
    ) AS content

FROM `{PROJECT_ID}.{DATASET}.fact_sales` AS f

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_customer` AS c
    ON f.customer_key = c.customer_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_product` AS p
    ON f.product_key = p.product_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
    ON f.date_key = d.date_key
"""

print("Creating RAG documents...")

job = client.query(create_documents_sql)
job.result()

print("✓ rag_documents created")


# ---------------------------------------------------------
# STEP 2: Generate embeddings
# ---------------------------------------------------------

create_embeddings_sql = f"""
CREATE OR REPLACE TABLE
`{PROJECT_ID}.{DATASET}.rag_embeddings` AS

SELECT
    record_id,
    content,

    AI.EMBED(
        content,
        endpoint => 'gemini-embedding-001',
        task_type => 'RETRIEVAL_DOCUMENT'
    ).result AS embedding

FROM `{PROJECT_ID}.{DATASET}.rag_documents`
"""

print("Generating embeddings...")

job = client.query(create_embeddings_sql)
job.result()

print("✓ Embeddings generated")
print("✓ rag_embeddings created")


# ---------------------------------------------------------
# STEP 3: Check the result
# ---------------------------------------------------------

check_sql = f"""
SELECT
    COUNT(*) AS total_records
FROM `{PROJECT_ID}.{DATASET}.rag_embeddings`
"""

result = client.query(check_sql).result()

for row in result:
    print(f"✓ Total embedded records: {row.total_records}")


print("\nRAG embedding pipeline completed successfully.")