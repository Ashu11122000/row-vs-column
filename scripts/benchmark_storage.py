
import gc
import time
import threading
import psutil
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pyarrow.compute as pc

from pathlib import Path

# File paths
CSV_FILE = Path("data/raw/ecommerce_1m.csv")
PARQUET_FILE = Path("data/processed/ecommerce_1m.parquet")

# Lookup target
TARGET_ID = 750000

process = psutil.Process()


def measure_operation(operation):
    """Measure execution time and approximate peak RSS increase."""

    gc.collect()

    baseline_memory = process.memory_info().rss
    peak_memory = [baseline_memory]

    stop_monitoring = threading.Event()

    def monitor_memory():
        while not stop_monitoring.is_set():
            current_memory = process.memory_info().rss
            peak_memory[0] = max(peak_memory[0], current_memory)
            stop_monitoring.wait(0.01)

    monitor = threading.Thread(target=monitor_memory)
    monitor.start()

    start_time = time.perf_counter()

    try:
        result = operation()
    finally:
        elapsed = time.perf_counter() - start_time
        peak_memory[0] = max(
            peak_memory[0],
            process.memory_info().rss
        )
        stop_monitoring.set()
        monitor.join()

    memory_increase = max(
        0,
        peak_memory[0] - baseline_memory
    ) / (1024 ** 2)

    return result, elapsed, memory_increase


# ------------------------------------------------
# CSV: Full-row lookup
# ------------------------------------------------

def csv_lookup():
    df = pd.read_csv(CSV_FILE)

    matching_rows = df.loc[
        df["record_id"] == TARGET_ID
    ]

    result = (
        matching_rows.iloc[0].to_dict()
        if not matching_rows.empty
        else None
    )

    del df, matching_rows

    return result


# ------------------------------------------------
# Parquet: Full-row lookup
# ------------------------------------------------

def parquet_lookup():
    dataset = ds.dataset(
        PARQUET_FILE,
        format="parquet"
    )

    table = dataset.to_table(
        columns=dataset.schema.names,
        filter=ds.field("record_id") == TARGET_ID
    )

    result = (
        table.slice(0, 1).to_pylist()[0]
        if table.num_rows > 0
        else None
    )

    del table

    return result


# ------------------------------------------------
# CSV: Average of one column
# ------------------------------------------------

def csv_aggregation():
    df = pd.read_csv(
        CSV_FILE,
        usecols=["float_1"]
    )

    result = df["float_1"].mean()

    del df

    return result


# ------------------------------------------------
# Parquet: Average of one column
# ------------------------------------------------

def parquet_aggregation():
    table = pq.read_table(
        PARQUET_FILE,
        columns=["float_1"]
    )

    result = pc.mean(table["float_1"]).as_py()

    del table

    return result


# ------------------------------------------------
# Execute benchmarks
# ------------------------------------------------

print("ROW VS COLUMN STORAGE BENCHMARK")
print("================================")

print("\n1. FULL-ROW LOOKUP")
print("------------------")

csv_row, csv_time, csv_memory = measure_operation(
    csv_lookup
)

print("CSV:")
print(f"Execution Time: {csv_time:.4f} seconds")
print(f"Peak Memory Increase: {csv_memory:.2f} MB")
print("Record Found:", csv_row is not None)

del csv_row
gc.collect()

parquet_row, parquet_time, parquet_memory = measure_operation(
    parquet_lookup
)

print("\nParquet:")
print(f"Execution Time: {parquet_time:.4f} seconds")
print(f"Peak Memory Increase: {parquet_memory:.2f} MB")
print("Record Found:", parquet_row is not None)

if csv_time > 0:
    print(
        "\nLookup Speed Ratio (CSV / Parquet):",
        f"{csv_time / parquet_time:.2f}x"
    )

del parquet_row
gc.collect()


print("\n2. SINGLE-COLUMN AGGREGATION")
print("----------------------------")

csv_avg, csv_agg_time, csv_agg_memory = measure_operation(
    csv_aggregation
)

print("CSV:")
print(f"Average: {csv_avg:.2f}")
print(f"Execution Time: {csv_agg_time:.4f} seconds")
print(f"Peak Memory Increase: {csv_agg_memory:.2f} MB")

parquet_avg, parquet_agg_time, parquet_agg_memory = measure_operation(
    parquet_aggregation
)

print("\nParquet:")
print(f"Average: {parquet_avg:.2f}")
print(f"Execution Time: {parquet_agg_time:.4f} seconds")
print(f"Peak Memory Increase: {parquet_agg_memory:.2f} MB")

print("\n3. FINAL COMPARISON")
print("-------------------")

print(f"CSV file size: {CSV_FILE.stat().st_size / (1024**2):.2f} MB")
print(
    f"Parquet file size: "
    f"{PARQUET_FILE.stat().st_size / (1024**2):.2f} MB"
)

print("\nBenchmark completed successfully!")
