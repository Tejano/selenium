#1. Test Fetching Metadata from the Database
#Validate that you can dynamically fetch metadata for the target table's numeric columns.

import pyodbc
import pandas as pd

# Connection string for Windows Authentication
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server_name;"
    "DATABASE=your_database_name;"
    "Trusted_Connection=yes;"
)

# Replace with the name of your target table
target_table = "dbo.TestTable"

conn = pyodbc.connect(connection_string)

# Query to fetch numeric metadata
query_metadata = f"""
SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{target_table.split('.')[-1]}' -- Strip schema if present
  AND DATA_TYPE IN ('numeric', 'decimal', 'float', 'real')
"""

metadata = pd.read_sql(query_metadata, conn)

print(f"Metadata for numeric columns in {target_table}:")
print(metadata)

conn.close()
