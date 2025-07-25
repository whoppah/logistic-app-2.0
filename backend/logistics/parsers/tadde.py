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
        Parse a Tadde PDF into a DataFrame of invoice lines, extracting:
          - Invoice number (F-YYYY-NNN)
          - Invoice date   (date)
          - order_number   (the whoppahXXX code)
          - Order ID       (UUID)
          - qty (int), unit_price (float), vat (int), price_tadde (float)
        """
        # Read all lines
        stream = io.BytesIO(file_bytes)
        lines: list[str] = []
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if not txt:
                    continue
                for ln in txt.split("\n"):
                    lines.append(ln.strip())

        # Pull header metadata
        invoice_number = None
        invoice_date   = None
        total_value    = None
        for ln in lines:
            if invoice_number is None:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_number = m.group(1)
                    print(f"\n [DEBUG] Invoice number is {invoice_number}")
            if invoice_date is None:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"\n [DEBUG] Invoice date is {invoice_date}")
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    raw = m.group(1).replace(",", "")
                    print(f"\n [DEBUG] Total value is {raw}")
                    try:
                        total_value = float(raw)
                    except ValueError:
                        total_value = None
            if invoice_number and invoice_date and total_value is not None:
                break

        #Scan for each “qty unit €… % €…” line
        data = []
        price_pattern = re.compile(r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)")
        uuid_pattern  = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
        whop_pattern  = re.compile(r"^(whoppah\d{3,})$", re.IGNORECASE)

        for i, ln in enumerate(lines):
            print(f"\n [DEBUG] line {i} is {ln}")
            qm = price_pattern.match(ln)
            if not qm:
                continue

            # extract qty/price
            qty        = int(qm.group(1))
            unit_price = float(qm.group(2).replace(",", "."))
            vat_pct    = int(qm.group(3))
            price_tadde= float(qm.group(4).replace(",", "."))

            # look backwards for whoppah code
            order_number = None
            for back in range(1, 6):
                if i - back < 0:
                    break
                m = whop_pattern.match(lines[i - back])
                if m:
                    order_number = m.group(1).lower()
                    break

            # look forwards for UUID
            order_id = None
            for fwd in range(1, 6):
                if i + fwd >= len(lines):
                    break
                uu = uuid_pattern.search(lines[i + fwd])
                if uu:
                    order_id = uu.group(0)
                    break

            # only if we found everything
            if order_number and order_id:
                data.append({
                    "Invoice number": invoice_number or "",
                    "Invoice date":   invoice_date,
                    "order_number":   order_number,
                    "Order ID":       order_id,
                    "qty":            qty,
                    "unit_price":     unit_price,
                    "vat":            vat_pct,
                    "price_tadde":    price_tadde,
                })

        #Build DataFrame
        df = pd.DataFrame(data)

        # coerce date
        if "Invoice date" in df.columns:
            df["Invoice date"] = pd.to_datetime(
                df["Invoice date"], dayfirst=True, errors="coerce"
            ).dt.date

        # sanity check totals
        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        # Validate & return
        self.validate(df)
        return df
