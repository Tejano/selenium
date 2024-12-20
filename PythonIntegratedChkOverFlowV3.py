import pyodbc
import pandas as pd
import re

# Step 1: Read the SQL File
sql_file_path = r"C:\path\to\your\insert_select.sql"
with open(sql_file_path, 'r') as file:
    sql_content = file.read()

print("Original SQL Content:")
print(sql_content)

# Step 2: Clean the SQL Content
sql_content_cleaned = re.sub(r"--.*", "", sql_content)  # Remove single-line comments
sql_content_cleaned = re.sub(r"/\*.*?\*/", "", sql_content_cleaned, flags=re.DOTALL)  # Remove multi-line comments

print("\nCleaned SQL Content:")
print(sql_content_cleaned)

# Step 3: Parse the INSERT INTO Statement
insert_pattern = re.search(
    r"INSERT INTO\s+([\w\.\[\]]+)\s*\((.*?)\)\s*SELECT",
    sql_content_cleaned,
    re.IGNORECASE | re.DOTALL
)
if not insert_pattern:
    print("Debug: Unable to match the INSERT INTO statement. Check the SQL content:")
    print(sql_content_cleaned)
    raise ValueError("The SQL file does not contain a valid INSERT INTO statement.")

target_table = insert_pattern.group(1).strip()
target_columns = [col.strip() for col in insert_pattern.group(2).split(",")] if insert_pattern.group(2) else None
print("\nTarget Table:", target_table)
print("Target Columns (Before Filtering):", target_columns)

# Step 4: Parse the SELECT Statement
select_pattern = re.search(
    r"SELECT\s+(.+?)\s+FROM\s+([\w\.\[\]]+)",
    sql_content_cleaned,
    re.IGNORECASE | re.DOTALL
)
if not select_pattern:
    print("Debug: Unable to match the SELECT statement. Check the SQL content:")
    print(sql_content_cleaned)
    raise ValueError("The SQL file does not contain a valid SELECT statement.")

select_columns_raw = select_pattern.group(1).strip()
source_table = select_pattern.group(2).strip()
select_columns = [col.strip() for col in select_columns_raw.split(",")]
print("\nSource Table:", source_table)
print("Raw SELECT Columns (Before Filtering):", select_columns)

# Step 5: Filter `NULL AS` Fields and Bound Fields
# Identify and exclude fields that are explicitly `NULL AS FieldName`
null_as_fields = [col for col in select_columns if re.match(r"NULL\s+AS\s+\w+", col, re.IGNORECASE)]
# Identify and exclude bound fields prefixed with table aliases (e.g., B.Field)
bound_fields = [col for col in select_columns if "." in col and not col.strip().startswith("CASE")]

# Exclude `NULL AS` and bound fields
excluded_fields = null_as_fields + bound_fields
filtered_select_columns = [col for col in select_columns if col not in excluded_fields]
filtered_target_columns = [col for i, col in enumerate(target_columns) if select_columns[i] not in excluded_fields]

print("\nFiltered SELECT Columns:", filtered_select_columns)
print("Filtered Target Columns:", filtered_target_columns)

# Step 6: Set up the Database Connection
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server_name;"
    "DATABASE=your_database_name;"
    "Trusted_Connection=yes;"
)
conn = pyodbc.connect(connection_string)

# Step 7: Fetch Metadata for Target Table
metadata_query = f"""
SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{target_table.split('.')[-1]}'
  AND DATA_TYPE IN ('numeric', 'decimal', 'float', 'real')
"""
metadata = pd.read_sql(metadata_query, conn)
print("\nMetadata for numeric columns in", target_table)
print(metadata)

# Step 8: Fetch Source Data
source_query = f"SELECT {', '.join(filtered_select_columns)} FROM {source_table}"
print("\nGenerated Source Query:")
print(source_query)

source_data = pd.read_sql(source_query, conn)
print("\nSource Data:")
print(source_data)

# Step 9: Validate Numeric Columns for Overflow
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

issues = []
for idx, row in source_data.iterrows():
    for _, col_meta in metadata.iterrows():
        target_column = col_meta['COLUMN_NAME']
        precision = col_meta['NUMERIC_PRECISION']
        scale = col_meta['NUMERIC_SCALE']

        # Map source column to target column
        if filtered_target_columns:
            source_column = next((filtered_select_columns[i] for i, col in enumerate(filtered_target_columns) if col == target_column), None)
        else:
            source_column = None

        if source_column:
            issue = validate_numeric(row, source_column, precision, scale)
            if issue:
                issues.append({"Row": idx, "Issue": issue})

# Step 10: Output Results
if issues:
    issues_df = pd.DataFrame(issues)
    print("\nValidation Issues Found:")
    print(issues_df)
    issues_df.to_csv("validation_issues.csv", index=False)  # Save to CSV
else:
    print("\nNo overflow issues found.")

# Cleanup
conn.close()
