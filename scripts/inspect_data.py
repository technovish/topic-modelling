import pandas as pd
import os

file_path = 'data/tmo_comments.xlsx'
if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        print("Columns found:", df.columns.tolist())
        print("\nFirst 3 rows:")
        print(df.head(3))
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print(f"File not found: {file_path}")
