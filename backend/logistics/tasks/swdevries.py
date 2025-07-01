#backend/logistics/tasks/swdevries.py
import pandas as pd
import io
from .base_parser import BaseParser


class SwdevriesParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        excel_stream = io.BytesIO(file_bytes)
        df = pd.read_excel(excel_stream, sheet_name="Blad1", header=None)

        invoice_value = df.iloc[1, 1]
        date_value = df.iloc[1, 0]
        total_value = df.iloc[-1, 3]

        df = df.iloc[:-1]  # Remove total row
        new_header = df.iloc[2]
        df = df[3:].copy()
        df.columns = new_header
        df.drop(columns=df.columns[df.columns.isna()], inplace=True)

        # Add metadata
        df["Invoice number"] = invoice_value
        df["Invoice date"] = pd.to_datetime(date_value, dayfirst=True, errors='coerce')
        df['Drop-off date'] = pd.to_datetime(df['Drop-off date'], dayfirst=True, errors='coerce')
        df['Pick-up date'] = pd.to_datetime(df['Pick-up date'], dayfirst=True, errors='coerce')

        df.rename(columns={"Price": "price_swdevries"}, inplace=True)
        df.columns = df.columns.str.strip()
        df.reset_index(drop=True, inplace=True)

        sum_price = round(df["price_swdevries"].sum(), 2)
        if abs(total_value - sum_price) > 0.01:
            print(f"[WARN] Total mismatch: Invoice says {total_value}, parsed sum is {sum_price}")
        else:
            print(f"[OK] Total matches: {sum_price}")

        self.validate(df)
        return df
