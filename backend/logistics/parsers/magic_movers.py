#backend/logistics/parsers/magic_movers.py
import pandas as pd
import io
from .base_parser import BaseParser


class MagicMoversParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        excel_stream = io.BytesIO(file_bytes)
        df = pd.read_excel(excel_stream, sheet_name="Arkusz1", header=1)

        invoice_value = df.iloc[1, 1]
        date_value = df.iloc[1, 0]
        total_value = df.iloc[-1, 3]

        df.drop(columns=["Unnamed: 0" ], inplace=True)
        total_value = df.iloc[-1,1]
        df.columns = df.columns.str.strip()  
        df.rename(columns={"Unnamed: 1": "Order ID MAGIC MOVERS", "Unnamed: 2": "price_magic_movers"}, inplace=True)
        df[['wooden', 'date', 'extra']] = df['Order ID MAGIC MOVERS'].str.extract(r'([A-Za-z/]+)(\d{8})/(\d+)')
        df['is_wooden'] = df['wooden'] == 'W/' #define is_wooden
        df = df.drop(columns=['wooden'])
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.iloc[:-2]
        return df
        
        # Add metadata
        df["Invoice number"] = invoice_value
        df["Invoice date"] = pd.to_datetime(date_value, dayfirst=True, errors='coerce')

        
        df.columns = df.columns.str.strip()
        df.reset_index(drop=True, inplace=True)
        sum_price = round(df["price_magic_movers"].sum(), 2)
        if abs(total_value - sum_price) > 0.01:
            print(f"[WARN] Total mismatch: Invoice says {total_value}, parsed sum is {sum_price}")
        else:
            print(f"[OK] Total matches: {sum_price}")

        self.validate(df)
        return df

    
