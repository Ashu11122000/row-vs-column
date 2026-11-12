
import numpy as np
import pandas as pd
from pathlib import Path

# Dataset configuration
TOTAL_ROWS = 1_000_000
BATCH_SIZE = 100_000
OUTPUT_FILE = Path("data/raw/ecommerce_1m.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# Sample string values
products = ["Laptop", "Mobile", "Tablet", "Monitor", "Keyboard"]
regions = ["North", "South", "East", "West"]
categories = ["Electronics", "Accessories", "Computers"]
statuses = ["Pending", "Shipped", "Delivered", "Cancelled"]
payment_methods = ["Card", "UPI", "Cash", "Net Banking"]

# Generate data in batches
for start in range(0, TOTAL_ROWS, BATCH_SIZE):

    rows = min(BATCH_SIZE, TOTAL_ROWS - start)

    data = {
        "record_id": np.arange(start + 1, start + rows + 1)
    }

    # 10 string columns
    data["product"] = rng.choice(products, rows)
    data["region"] = rng.choice(regions, rows)
    data["category"] = rng.choice(categories, rows)
    data["status"] = rng.choice(statuses, rows)
    data["payment_method"] = rng.choice(payment_methods, rows)
    data["customer_type"] = rng.choice(["New", "Returning"], rows)
    data["sales_channel"] = rng.choice(["Online", "Store"], rows)
    data["shipping_type"] = rng.choice(["Standard", "Express"], rows)
    data["priority"] = rng.choice(["Low", "Medium", "High"], rows)
    data["country"] = rng.choice(["India", "USA", "UK", "Canada"], rows)

    # 20 integer columns
    for i in range(1, 21):
        data[f"integer_{i}"] = rng.integers(1, 10000, rows)

    # 10 boolean columns
    for i in range(1, 11):
        data[f"boolean_{i}"] = rng.choice([True, False], rows)

    # 9 float columns
    for i in range(1, 10):
        data[f"float_{i}"] = np.round(
            rng.uniform(1, 100000, rows), 2
        )

    df = pd.DataFrame(data)

    # Append each batch to CSV
    df.to_csv(
        OUTPUT_FILE,
        mode="w" if start == 0 else "a",
        header=(start == 0),
        index=False
    )

    print(
        f"Generated {start + rows:,} / {TOTAL_ROWS:,} records"
    )

    del df, data

print("\nDataset generation completed!")
print("Total rows:", TOTAL_ROWS)
print("Total columns:", len(pd.read_csv(OUTPUT_FILE, nrows=0).columns))
print("Output file:", OUTPUT_FILE)
print(
    "File size:",
    round(OUTPUT_FILE.stat().st_size / (1024 ** 2), 2),
    "MB"
)
