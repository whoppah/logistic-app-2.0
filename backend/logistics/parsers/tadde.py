# backend/logistics/parsers/tadde.py
import io
import re
import pandas as pd
import pdfplumber
from datetime import datetime, date
from .base_parser import BaseParser

class TaddeParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        """
        Parse a Tadde PDF into a DataFrame of shipment rows, extracting:
          - invoice_number (str)
          - invoice_date   (date)
          - order_number   (str)  ← the 14-digit line code
          - order_id       (uuid)
          - qty (int), unit_price (float), vat (int), price_tadde (float)
        """
        stream = io.BytesIO(file_bytes)
        lines = []
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))

        invoice_number = None
        invoice_date   = None
        total_value    = None

        for line in lines:
            print("[DEBUG] line:",line)
            if not invoice_number and "Invoice number" in line:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", line)
                if m:
                    invoice_number = m.group(1)
                    print(f"[DEBUG] Invoice number {invoice_number}")
            if not invoice_date and "Issue date" in line:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", line)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"[DEBUG] Invoice date {invoice_date}")
            if total_value is None and "Total" in line and "excl. VAT" in line:
                m = re.search(r"€\s*([\d\.,]+)", line)
                if m:
                    raw = m.group(1).replace(",","")
                    try:
                        total_value = float(raw)
                         print("[DEBUG] total_value is ",total_value)
                    except ValueError:
                        total_value = None
            if invoice_number and invoice_date and total_value is not None:
                break

        data = []
        i = 0
        while i < len(lines):
            ln = lines[i].strip().replace("*", "")
            m = re.match(
                r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)",
                ln
            )
            if m:
                qty          = int(m.group(1))
                unit_price   = float(m.group(2).replace(",", "."))
                vat_pct      = int(m.group(3))
                total_excl   = float(m.group(4).replace(",", "."))
                order_id     = ""
                order_number = ""
                for offset in range(1, 6):
                    if i + offset >= len(lines):
                        break
                    nxt = lines[i + offset]
                    uu = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", nxt)
                    if uu and not order_id:
                        order_id = uu.group(0)
                    
                    ref = re.search(r"\b(\d{14,})\b", nxt)
                    if ref and not order_number:
                        order_number = ref.group(1)
                    if order_id and order_number:
                        break

                data.append({
                    "Invoice number": invoice_number,
                    "Invoice date":   invoice_date,
                    "order_number":   order_number,
                    "Order ID":       order_id,
                    "qty":            qty,
                    "unit_price":     unit_price,
                    "vat":            vat_pct,
                    "price_tadde":    total_excl,
                })
                i += 1
                continue

            i += 1

        df = pd.DataFrame(data)

        if "Invoice date" in df.columns and df["Invoice date"].dtype == object:
            df["Invoice date"] = pd.to_datetime(
                df["Invoice date"], dayfirst=True, errors="coerce"
            ).dt.date

        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        self.validate(df)
        return df
