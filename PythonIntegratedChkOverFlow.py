import pyodbc
import pandas as pd
import re

# Step 1: Read and Parse the SQL File
sql_file_path = r"C:\path\to\your\insert_select.sql"
with open(sql_file_path, 'r') as file:
    sql_content = file.read()

print("SQL Content:")
print(sql_content)
sql_content_cleaned = re.sub(r"--.*", "", sql_content)  # Remove single-line comments
sql_content_cleaned = re.sub(r"/\*.*?\*/", "", sql_content_cleaned, flags=re.DOTALL)  # Remove multi-line comments

# Debugging: Print cleaned SQL content
print("Cleaned SQL Content:")
print(sql_content_cleaned)

# Parse INSERT INTO for Target Table and Columns
insert_pattern = re.search(
    r"INSERT INTO\s+([\w\.\[\]]+)\s*\((.*?)\)\s*SELECT",
    sql_content,
    re.IGNORECASE | re.DOTALL
)
if not insert_pattern:
    print("Debug: Unable to match the INSERT INTO statement. Check the SQL content:")
    print(sql_content)
    raise ValueError("The SQL file does not contain a valid INSERT INTO statement.")

target_table = insert_pattern.group(1).strip()
target_columns = [col.strip() for col in insert_pattern.group(2).split(",")] if insert_pattern.group(2) else None
print(f"Target Table: {target_table}")
print(f"Target Columns: {target_columns if target_columns else 'No columns specified'}")

# Parse SELECT Statement for Source Table and Columns
select_pattern = re.search(
    r"SELECT\s+(.+?)\s+FROM\s+([\w\.\[\]]+)",
    sql_content,
    re.IGNORECASE | re.DOTALL
)
if not select_pattern:
    print("Debug: Unable to match the SELECT statement. Check the SQL content:")
    print(sql_content)
    raise ValueError("The SQL file does not contain a valid SELECT statement.")

#select_columns = [col.strip() for col in select_pattern.group(1).split(",")]
select_columns_raw = select_pattern.group(1).strip()
source_table = select_pattern.group(2).strip()

# Process the SELECT columns safely
select_columns = [col.strip() for col in select_columns_raw.split(",")]

# Debugging: Print parsed columns and generated query
print("Debug: Parsed SELECT Columns:")
print(select_columns)
print(f"Source Table: {source_table}")



# Step 2: Set up the database connection
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server_name;"
    "DATABASE=your_database_name;"
    "Trusted_Connection=yes;"
)
conn = pyodbc.connect(connection_string)

# Step 3: Fetch Metadata for Target Table
metadata_query = f"""
SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{target_table.split('.')[-1]}'
  AND DATA_TYPE IN ('numeric', 'decimal', 'float', 'real')
"""
metadata = pd.read_sql(metadata_query, conn)
print(f"Metadata for numeric columns in {target_table}:")
print(metadata)

# Step 4: Fetch Source Data
source_query = f"SELECT {', '.join(select_columns)} FROM {source_table}"
print("Debug: Generated Source Query:")
print(source_query)
source_data = pd.read_sql(source_query, conn)
print("Source Data:")
print(source_data)

# Step 5: Validate Numeric Columns for Overflow
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
        if target_columns:
            source_column = next((select_columns[i] for i, col in enumerate(target_columns) if col == target_column), None)
        else:
            source_column = None

        if source_column:
            issue = validate_numeric(row, source_column, precision, scale)
            if issue:
                issues.append({"Row": idx, "Issue": issue})

# Step 6: Output Results
if issues:
    issues_df = pd.DataFrame(issues)
    print("Validation Issues Found:")
    print(issues_df)
    issues_df.to_csv("validation_issues.csv", index=False)  # Save to CSV
else:
    print("No overflow issues found.")

# Cleanup
conn.close()
