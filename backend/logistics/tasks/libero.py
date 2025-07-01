#backend/logistics/tasks/libero.py
import pandas as pd
import pdfplumber
import io
import re
from .base_parser import BaseParser


class LiberoParser(BaseParser):
    def parse(self, file_bytes: bytes, context: dict = None) -> pd.DataFrame:
        """
        context must include:
        {
            'pdf_bytes': bytes
        }
        """
        if not context or "pdf_bytes" not in context:
            raise ValueError("Missing PDF metadata context for Libero invoice.")

        invoice_date, invoice_num = self._parse_pdf(context["pdf_bytes"])

        excel_stream = io.BytesIO(file_bytes)
        df = pd.read_excel(excel_stream, sheet_name="factuur 14-03")

        total_value = float(df.iloc[-3, 1].replace(".", "").replace(",-", "."))

        df["Invoice number"] = invoice_num
        df["Invoice date"] = pd.to_datetime(invoice_date, dayfirst=True, errors='coerce')
        df.columns = df.columns.str.strip()
        df.drop(columns=["#", "BTW 21%", "Totaal"], inplace=True)

        df.rename(columns={
            "LL Bumbal ref.": "Order number LIBERO",
            "Leverdatum": "date",
            "Omschrijving": "Order ID",
            "Bedrag": "price_libero_logistics"
        }, inplace=True)

        df['price_libero_logistics'] = df['price_libero_logistics'].astype(str).str.replace(',-', '', regex=True).astype(float)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        df = df.iloc[:-5]

        sum_price = round(df["price_libero_logistics"].sum(), 2)
        if abs(total_value - sum_price) > 0.01:
            print(f"[WARN] Total mismatch: Invoice says {total_value}, parsed sum is {sum_price}")
        else:
            print(f"[OK] Total matches: {sum_price}")

        self.validate(df)
        return df

    def _parse_pdf(self, pdf_bytes: bytes):
        stream = io.BytesIO(pdf_bytes)
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                for line in text.split("\n"):
                    line = line.strip()
                    match = re.search(r"Factuurnummer:\s*(\S+)\s+Factuurdatum:\s*(\d{2}-\d{2}-\d{4})", line)
                    if match:
                        return match.group(2), match.group(1)  # (date, number)
        return "", ""
