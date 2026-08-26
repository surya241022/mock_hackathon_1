from google.cloud import bigquery


PROJECT_ID = "mock-trail-project-1"
DATASET = "gold"

client = bigquery.Client(project=PROJECT_ID)


query = f"""
CREATE OR REPLACE TABLE
`{PROJECT_ID}.{DATASET}.ml_high_value_orders` AS

SELECT
    f.quantity,
    f.unit_price,
    c.state,
    p.category,
    f.payment_method,

    CASE
        WHEN f.total_sales >= 10000 THEN 1
        ELSE 0
    END AS high_value_order

FROM `{PROJECT_ID}.{DATASET}.fact_sales` AS f

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_customer` AS c
    ON f.customer_key = c.customer_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_product` AS p
    ON f.product_key = p.product_key
"""


print("Creating ML training table...")

job = client.query(query)
job.result()

print("✓ ML training table created")


# Verify the table
check_query = f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET}.ml_high_value_orders`
LIMIT 10
"""

print("\nSample training data:")

results = client.query(check_query).result()

for row in results:
    print(dict(row))
