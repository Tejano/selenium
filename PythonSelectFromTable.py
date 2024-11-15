
#2. Test Source Data Query
#Ensure you can fetch source data using the parsed columns and table name.
import pyodbc
import pandas as pd

# Connection string for Windows Authentication
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server_name;"
    "DATABASE=your_database_name;"
    "Trusted_Connection=yes;"
)

# Replace with your source table and columns
source_table = "Broker.dbo.CommGroups"
source_columns = ["Field1", "Field2", "Field3", "Field4"]

conn = pyodbc.connect(connection_string)

# Query the source data
source_query = f"SELECT {', '.join(source_columns)} FROM {source_table}"
source_data = pd.read_sql(source_query, conn)

print("Source Data:")
print(source_data)

conn.close()
