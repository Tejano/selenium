import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count

# Simulate Source Data
num_rows = 727559
num_cols = 69
source_data = pd.DataFrame(np.random.random(size=(num_rows, num_cols)), columns=[f'Col{i}' for i in range(num_cols)])

# Simulate Metadata
metadata = pd.DataFrame({
    "COLUMN_NAME": [f"Col{i}" for i in range(num_cols)],
    "NUMERIC_PRECISION": [10] * num_cols,
    "NUMERIC_SCALE": [2] * num_cols
})

# Vectorized Validation Function
def validate_chunk(chunk):
    issues = []
    for _, col_meta in metadata.iterrows():
        column = col_meta['COLUMN_NAME']
        precision = col_meta['NUMERIC_PRECISION']
        scale = col_meta['NUMERIC_SCALE']
        max_value = 10 ** (precision - scale) - 10 ** -scale
        min_value = -max_value

        # Vectorized validation
        invalid_rows = chunk[(chunk[column] < min_value) | (chunk[column] > max_value)]
        for idx, row in invalid_rows.iterrows():
            issues.append({"Row": idx, "Column": column, "Value": row[column], "Issue": "Numeric Overflow"})
    return issues

# Parallel Processing Function
def process_in_parallel(data, func, num_partitions):
    # Split data into partitions
    data_split = np.array_split(data, num_partitions)
    
    with Pool(processes=num_partitions) as pool:
        results = pool.map(func, data_split)
    return [item for sublist in results for item in sublist]  # Flatten the results

# Number of CPU cores
num_cores = cpu_count()

# Run Validation with Parallelization
issues = process_in_parallel(source_data, validate_chunk, num_cores)

# Output Results
issues_df = pd.DataFrame(issues)
print("Validation Issues Found:")
print(issues_df)
