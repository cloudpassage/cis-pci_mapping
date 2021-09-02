import os
import pandas as pd


class ExcelHandler:

    def read_from_excel(self, sheet_name, file_name, base_dir, excel_engine_type):
        excel_file_path = os.path.join(base_dir, file_name)
        xlsx = pd.ExcelFile(excel_file_path)
        df = pd.read_excel(xlsx, sheet_name, engine=excel_engine_type)
        return df
