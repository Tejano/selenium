import os
import shutil
import pandas as pd
import win32com.client

# ✅ Default Paths (User can change at runtime)
DEFAULT_TEMPLATE_PATH = r"C:\mip_templates\template.xlsx"
DEFAULT_SOURCE_FOLDER = r"C:\path\to\source"
DEFAULT_DEST_FOLDER = r"C:\path\to\destination"

# ✅ Allow user to change paths
template_path = input(f"Enter template path [{DEFAULT_TEMPLATE_PATH}]: ").strip() or DEFAULT_TEMPLATE_PATH
source_folder = input(f"Enter source folder [{DEFAULT_SOURCE_FOLDER}]: ").strip() or DEFAULT_SOURCE_FOLDER
dest_folder = input(f"Enter destination folder [{DEFAULT_DEST_FOLDER}]: ").strip() or DEFAULT_DEST_FOLDER

# ✅ Ensure destination folder exists
os.makedirs(dest_folder, exist_ok=True)

# ✅ Define Special Formatting Rules
TEXT_COLUMNS = ["ID", "Code", "SerialNumber"]  # These should remain as text (leading zeros)
CURRENCY_COLUMNS = ["Price", "Amount", "TotalCost"]  # Currency values
DATE_COLUMNS = ["OrderDate", "ShipmentDate"]  # Date values

def detect_delimiter(file_path):
    """Detect whether the file is tab-delimited or comma-delimited"""
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
        if "\t" in first_line:
            return "\t"
        else:
            return ","

def convert_xls_to_xlsx(file_path):
    try:
        # ✅ Step 1: Copy the MIP-labeled template
        new_xlsx_path = os.path.join(dest_folder, os.path.basename(file_path).replace(".xls", ".xlsx"))
        shutil.copy(template_path, new_xlsx_path)

        # ✅ Step 2: Detect delimiter and read the file
        delimiter = detect_delimiter(file_path)
        df = pd.read_csv(file_path, delimiter=delimiter, dtype=str, encoding="utf-8", low_memory=False)

        # ✅ Step 3: Open the copied MIP-labeled template in Excel
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False  # Run in background
        excel.DisplayAlerts = False  # Disable pop-ups

        wb = excel.Workbooks.Open(new_xlsx_path)
        ws = wb.Sheets(1)  # First sheet

        # ✅ Step 4: Copy data into the template (handle all formats)
        for row_idx, row in enumerate(df.itertuples(index=False), start=1):
            for col_idx, (column_name, cell_value) in enumerate(zip(df.columns, row), start=1):
                if pd.isna(cell_value) or cell_value.strip() == "":
                    ws.Cells(row_idx, col_idx).Value = ""
                elif column_name in TEXT_COLUMNS:  # Force text format (preserve leading zeros)
                    ws.Cells(row_idx, col_idx).NumberFormat = "@"
                    ws.Cells(row_idx, col_idx).Value = cell_value
                elif column_name in CURRENCY_COLUMNS:  # Format as currency
                    ws.Cells(row_idx, col_idx).NumberFormat = "$#,##0.00"
                    ws.Cells(row_idx, col_idx).Value = float(cell_value.replace(",", "").replace("$", ""))
                elif column_name in DATE_COLUMNS:  # Format as date
                    ws.Cells(row_idx, col_idx).NumberFormat = "mm/dd/yyyy"
                    try:
                        ws.Cells(row_idx, col_idx).Value = pd.to_datetime(cell_value).strftime("%m/%d/%Y")
                    except:
                        ws.Cells(row_idx, col_idx).Value = cell_value  # Fallback if parsing fails
                elif cell_value.startswith("0") and cell_value.isdigit():  # Keep leading zeros
                    ws.Cells(row_idx, col_idx).NumberFormat = "@"
                    ws.Cells(row_idx, col_idx).Value = cell_value
                elif "E" in cell_value or "e" in cell_value:  # Convert exponential numbers
                    ws.Cells(row_idx, col_idx).NumberFormat = "0"
                    ws.Cells(row_idx, col_idx).Value = float(cell_value)
                else:  # Default case (numeric values)
                    ws.Cells(row_idx, col_idx).Value = cell_value

        # ✅ Step 5: Save the formatted file (MIP label stays from template)
        wb.Save()
        wb.Close()
        excel.Quit()

        print(f"✅ Converted and labeled file: {new_xlsx_path}")

    except Exception as e:
        print(f"❌ ERROR converting {file_path}: {e}")

# ✅ Process all `.xls` files
for file in os.listdir(source_folder):
    if file.endswith(".xls"):
        convert_xls_to_xlsx(os.path.join(source_folder, file))

print("✅ All files processed!")
