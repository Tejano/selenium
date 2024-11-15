#3. Test Numeric Validation Logic
#Test the logic for detecting overflow or invalid numeric values.


import pandas as pd

# Simulated source data
data = {
    "Field1": [12345.67, -9999.99, 0, 1000000000.0],
    "Field2": [0.1, 0.00001, -0.0001, 1.2],
}
source_data = pd.DataFrame(data)

# Simulated target metadata
metadata = pd.DataFrame({
    "COLUMN_NAME": ["Field1", "Field2"],
    "NUMERIC_PRECISION": [10, 5],
    "NUMERIC_SCALE": [2, 3],
})

def validate_numeric(row, source_column, precision, scale):
    try:
        max_value = 10 ** (precision - scale) - 10 ** -scale
        min_value = -max_value
        value = float(row[source_column])
        if not (min_value <= value <= max_value):
            return f"Overflow in {source_column} with value {value}"
    except Exception as e:
        return f"Invalid data in {source_column} with value {row[source_column]}: {e}"
    return None

# Validate
issues = []
for idx, row in source_data.iterrows():
    for _, col_meta in metadata.iterrows():
        target_column = col_meta['COLUMN_NAME']
        precision = col_meta['NUMERIC_PRECISION']
        scale = col_meta['NUMERIC_SCALE']

        issue = validate_numeric(row, target_column, precision, scale)
        if issue:
            issues.append({"Row": idx, "Issue": issue})

# Output issues
if issues:
    issues_df = pd.DataFrame(issues)
    print("Validation Issues:")
    print(issues_df)
else:
    print("No validation issues.")
