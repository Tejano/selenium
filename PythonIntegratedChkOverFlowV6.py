import pyodbc
import pandas as pd
import re
import logging
from datetime import datetime

# Generate a timestamped log file name
log_filename = f"validation_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Script started.")

# Step 1: Read the SQL File
sql_file_path = r"C:\path\to\your\insert_select.sql"
try:
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()
    logging.info("SQL file read successfully.")
except Exception as e:
    logging.error(f"Error reading SQL file: {e}")
    raise

logging.info("Original SQL Content:")
logging.info(sql_content)

# Step 2: Clean the SQL Content
sql_content_cleaned = re.sub(r"--.*", "", sql_content)  # Remove single-line comments
sql_content_cleaned = re.sub(r"/\*.*?\*/", "", sql_content_cleaned, flags=re.DOTALL)  # Remove multi-line comments
logging.info("Cleaned SQL Content:")
logging.info(sql_content_cleaned)

# Step 3: Parse the INSERT INTO Statement
insert_pattern = re.search(
    r"INSERT INTO\s+([\w\.\[\]]+)\s*\((.*?)\)\s*SELECT",
    sql_content_cleaned,
    re.IGNORECASE | re.DOTALL
)
if not insert_pattern:
    logging.error("Unable to match the INSERT INTO statement. Check the SQL content.")
    raise ValueError("The SQL file does not contain a valid INSERT INTO statement.")

target_table = insert_pattern.group(1).strip()
target_columns = [col.strip() for col in insert_pattern.group(2).split(",")] if insert_pattern.group(2) else None
logging.info(f"Target Table: {target_table}")
logging.info(f"Target Columns (Before Filtering): {target_columns}")

# Step 4: Parse the SELECT Statement
select_pattern = re.search(
    r"SELECT\s+(.+?)\s+FROM\s+([\w\.\[\]]+)",
    sql_content_cleaned,
    re.IGNORECASE | re.DOTALL
)
if not select_pattern:
    logging.error("Unable to match the SELECT statement. Check the SQL content.")
    raise ValueError("The SQL file does not contain a valid SELECT statement.")

select_columns_raw = select_pattern.group(1).strip()
source_table = select_pattern.group(2).strip()
select_columns = [col.strip() for col in select_columns_raw.split(",")]
logging.info(f"Source Table: {source_table}")
logging.info(f"Raw SELECT Columns (Before Filtering): {select_columns}")

# Step 5: Map Source Fields to Target Fields

# Filter NULL AS fields and bounded fields
null_as_fields = [col for col in select_columns if re.match(r"NULL\s+AS\s+\w+", col, re.IGNORECASE)]
bound_fields = [col for col in select_columns if "." in col]  # Fields with `.` are considered bound

excluded_fields = null_as_fields + bound_fields

# Log excluded fields for debugging
logging.info(f"Excluded Fields: {excluded_fields}")

# Filter out excluded fields
filtered_select_columns = [col for col in select_columns if col not in excluded_fields]
filtered_target_columns = [col for i, col in enumerate(target_columns) if select_columns[i] not in excluded_fields]

logging.info(f"Filtered SELECT Columns: {filtered_select_columns}")
logging.info(f"Filtered Target Columns: {filtered_target_columns}")

# Map filtered source fields to target fields
if len(filtered_target_columns) != len(filtered_select_columns):
    logging.error("Mismatch between filtered target and source column counts.")
    raise ValueError("The number of filtered target columns does not match the number of filtered source columns.")

field_mapping = dict(zip(filtered_target_columns, filtered_select_columns))
logging.info(f"Field Mapping After Filtering: {field_mapping}")


# Step 6: Set up the Database Connection
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server_name;"
    "DATABASE=your_database_name;"
    "Trusted_Connection=yes;"
)
try:
    conn = pyodbc.connect(connection_string)
    logging.info("Database connection established.")
except Exception as e:
    logging.error(f"Database connection error: {e}")
    raise

# Step 7: Fetch Metadata for Target Table
metadata_query = f"""
SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{target_table.split('.')[-1]}'
  AND DATA_TYPE IN ('numeric', 'decimal', 'float', 'real')
"""
try:
    metadata = pd.read_sql(metadata_query, conn)
    logging.info("Metadata fetched successfully.")
    logging.info(metadata)
except Exception as e:
    logging.error(f"Error fetching metadata: {e}")
    raise

# Step 8: Fetch Source Data
source_query = f"SELECT {', '.join(select_columns)} FROM {source_table}"
logging.info(f"Generated Source Query: {source_query}")

try:
    source_data = pd.read_sql(source_query, conn)
    logging.info(f"Source data fetched successfully. Total rows: {len(source_data)}")
except Exception as e:
    logging.error(f"Error fetching source data: {e}")
    raise

# Step 9: Validate Numeric Columns for Precision/Scale Mismatches
issues = []
try:
    for _, col_meta in metadata.iterrows():
        target_column = col_meta['COLUMN_NAME']
        precision = col_meta['NUMERIC_PRECISION']
        scale = col_meta['NUMERIC_SCALE']
        max_value = 10 ** (precision - scale) - 10 ** -scale
        min_value = -max_value

        source_column = field_mapping.get(target_column)

        if source_column in source_data.columns:
            logging.info(f"Validating column: {source_column} -> {target_column} with range {min_value} to {max_value}")
            
            # Identify out-of-range rows
            invalid_rows = source_data[(source_data[source_column] < min_value) | (source_data[source_column] > max_value)]
            logging.info(f"Invalid rows for column {source_column} ({target_column}): {len(invalid_rows)}")
            
            # Log issues for each invalid row
            for idx, row in invalid_rows.iterrows():
                issues.append({
                    "Row": idx,
                    "Source Column": source_column,
                    "Target Column": target_column,
                    "Value": row[source_column],
                    "Valid Range": f"{min_value} to {max_value}",
                    "Issue": "Numeric Overflow"
                })
        else:
            logging.warning(f"Source column {source_column} does not exist for target column {target_column}")
except Exception as e:
    logging.error(f"Error during validation: {e}")
    raise

# Step 10: Output Results
if issues:
    issues_df = pd.DataFrame(issues)
    logging.info("Validation Issues Found:")
    logging.info(issues_df)
    issues_df.to_csv("validation_issues.csv", index=False)  # Save to CSV
else:
    logging.info("No overflow issues found.")

# Cleanup
conn.close()
logging.info("Script completed.")

