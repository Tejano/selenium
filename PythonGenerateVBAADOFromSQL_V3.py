import re

def read_sql_from_file(file_path):
    """
    Reads the contents of a SQL file.
    Args:
        file_path (str): Path to the SQL file.
    Returns:
        str: The SQL code as a string.
    """
    with open(file_path, "r", encoding="utf-8") as sql_file:
        return sql_file.read()

def clean_sql(sql_statement):
    """
    Cleans the SQL statement by removing comments and ensuring proper formatting.
    Args:
        sql_statement (str): The raw SQL/SP code.
    Returns:
        str: The cleaned SQL statement.
    """
    # Remove single-line comments (-- comment)
    sql_statement = re.sub(r"--.*", "", sql_statement)
    # Remove multi-line comments (/* comment */)
    sql_statement = re.sub(r"/\*.*?\*/", "", sql_statement, flags=re.DOTALL)
    # Remove excessive whitespace
    sql_statement = re.sub(r"\s+", " ", sql_statement.strip())
    return sql_statement

def split_long_string(long_string, max_length=100):
    """
    Splits a long string into multiple lines for VBA compatibility.
    Args:
        long_string (str): The long string to be split.
        max_length (int): Maximum length of each line.
    Returns:
        str: The formatted string with VBA line continuation.
    """
    chunks = [long_string[i:i + max_length] for i in range(0, len(long_string), max_length)]
    return " & _\n    ".join([f'"{chunk}"' for chunk in chunks])

def sql_to_vb_ado(sql_statement, sub_name="GeneratedSub", conn_name="conn"):
    """
    Converts a complex SQL stored procedure to a VB ADO Subroutine with dynamic parameters.
    Args:
        sql_statement (str): The SQL/SP code to be converted.
        sub_name (str): Name of the generated VB Subroutine.
        conn_name (str): Name of the VB ADO connection object.
    Returns:
        str: The VB ADO Subroutine as a string.
    """
    sql_cleaned = clean_sql(sql_statement)
    formatted_sql = split_long_string(sql_cleaned)

    vb_code = f"""
Sub {sub_name}(ByVal startMonth As Integer, ByVal endMonth As Integer)
    Dim {conn_name} As ADODB.Connection
    Dim rs As ADODB.Recordset
    Dim sql As String

    ' SQL Statement with dynamic parameters
    sql = "DECLARE @start_month INT = " & startMonth & ";" & _
          " DECLARE @end_month INT = " & endMonth & ";" & _
          {formatted_sql}

    ' Initialize connection
    Set {conn_name} = New ADODB.Connection
    {conn_name}.ConnectionString = "Your_Connection_String_Here"
    {conn_name}.Open

    ' Execute SQL
    On Error Resume Next
    Set rs = {conn_name}.Execute(sql)

    ' Check for results and process recordset
    If Not rs Is Nothing Then
        Do While Not rs.EOF
            Debug.Print rs.Fields(0).Value ' Replace with your field processing
            rs.MoveNext
        Loop
        rs.Close
        Set rs = Nothing
    End If

    ' Cleanup
    {conn_name}.Close
    Set conn_name = Nothing
End Sub
"""
    return vb_code

def write_to_file(output_file_path, content):
    """
    Writes the given content to a file.
    Args:
        output_file_path (str): Path to the output file.
        content (str): The content to write to the file.
    """
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(content)

def main():
    """
    Main execution flow: reads SQL file, processes it, and generates VBA code.
    """
    sql_file_path = "example.sql"  # Replace with your SQL file path
    output_file_path = "GeneratedVBA.bas"  # Replace with your desired output file path

    sql_statement = read_sql_from_file(sql_file_path)  # Read SQL file content
    generated_vba = sql_to_vb_ado(sql_statement, sub_name="ProcessSales", conn_name="conn")  # Generate VBA code

    print(generated_vba)  # Print the VBA code to the console
    write_to_file(output_file_path, generated_vba)  # Write the VBA code to a .bas file

if __name__ == "__main__":
    main()
