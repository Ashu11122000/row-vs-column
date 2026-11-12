
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
from pathlib import Path

# Input and output paths
input_file = Path("data/raw/ecommerce_1m.csv")
output_file = Path("data/processed/ecommerce_1m.parquet")

output_file.parent.mkdir(parents=True, exist_ok=True)

# Read CSV in batches to control memory usage
reader = csv.open_csv(
    input_file,
    read_options=csv.ReadOptions(
        block_size=16 * 1024 * 1024
    )
)

# Read the first batch to determine the schema
first_batch = reader.read_next_batch()

# Create Parquet writer
writer = pq.ParquetWriter(
    output_file,
    first_batch.schema,
    compression="snappy"
)

total_rows = 0

try:
    # Write first batch
    writer.write_batch(first_batch)
    total_rows += first_batch.num_rows

    print(f"Converted {total_rows:,} rows")

    # Write remaining batches
    for batch in reader:
        writer.write_batch(batch)
        total_rows += batch.num_rows

        print(f"Converted {total_rows:,} rows")

finally:
    writer.close()

# File size comparison
csv_size = input_file.stat().st_size
parquet_size = output_file.stat().st_size

print("\nConversion completed!")
print("----------------------")
print("Total rows:", total_rows)
print("CSV size:", round(csv_size / (1024 ** 2), 2), "MB")
print(
    "Parquet size:",
    round(parquet_size / (1024 ** 2), 2),
    "MB"
)

print(
    "Storage reduction:",
    round((1 - parquet_size / csv_size) * 100, 2),
    "%"
)

print("\nParquet schema:")
print(pq.read_schema(output_file))
