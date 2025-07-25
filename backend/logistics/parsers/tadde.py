# backend/logistics/parsers/tadde.py
import io
import re
import pandas as pd
import pdfplumber
from datetime import datetime
from .base_parser import BaseParser

class TaddeParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        """
        Parse a Tadde PDF into a DataFrame of invoice lines, extracting:
          - Invoice number (F-YYYY-NNN)
          - Invoice date   (date)
          - order_number   (whoppahXXX code)
          - Order ID       (UUID)
          - qty (int), unit_price (float), vat (int), price_tadde (float)
        """
        # 1) read all lines
        pdf_stream = io.BytesIO(file_bytes)
        lines: list[str] = []
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for ln in text.split("\n"):
                    ln = ln.strip()
                    if ln:
                        lines.append(ln)

        # 2) pull header metadata
        invoice_number = None
        invoice_date   = None
        total_value    = None
        for ln in lines:
            if invoice_number is None:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_number = m.group(1)
                    print(f"[DEBUG] Invoice number: {invoice_number}")
            if invoice_date is None:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"[DEBUG] Invoice date: {invoice_date}")
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    raw = m.group(1).replace(",", "")
                    try:
                        total_value = float(raw)
                        print(f"[DEBUG] Total excl. VAT: {total_value}")
                    except ValueError:
                        total_value = None
            if invoice_number and invoice_date and total_value is not None:
                break

        # 3) compile regexes
        price_re = re.compile(r"(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s*%\s*€\s*([\d\.,]+)", re.IGNORECASE)
        uuid_re  = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
        whop_re  = re.compile(r"whoppah\d{3,}", re.IGNORECASE)

        # 4) walk lines and extract rows
        data = []
        n = len(lines)
        for i, ln in enumerate(lines):
            print(f"[DEBUG] line {i} is: {ln}")
            if "unit €" not in ln.lower():
                continue

            pm = price_re.search(ln)
            if not pm:
                print(f"[WARN] price pattern not found in line {i}")
                continue

            qty        = int(pm.group(1))
            unit_price = float(pm.group(2).replace(",", "."))
            vat_pct    = int(pm.group(3))
            price_tad  = float(pm.group(4).replace(",", "."))

            # search ±6 lines for whoppah code & UUID
            lo, hi = max(0, i-6), min(n, i+7)
            order_number = None
            order_id     = None
            for j in range(lo, hi):
                if order_number is None:
                    wm = whop_re.search(lines[j])
                    if wm:
                        order_number = wm.group(0).lower()
                if order_id is None:
                    uu = uuid_re.search(lines[j])
                    if uu:
                        order_id = uu.group(0)
                if order_number and order_id:
                    break

            if not order_number or not order_id:
                print(
                    f"[WARN] skipping line {i}: "
                    f"{'no whoppah code ' if not order_number else ''}"
                    f"{'no UUID' if not order_id else ''}"
                )
                continue

            data.append({
                "Invoice number": invoice_number or "",
                "Invoice date":   invoice_date,
                "order_number":   order_number,
                "Order ID":       order_id,
                "qty":            qty,
                "unit_price":     unit_price,
                "vat":            vat_pct,
                "price_tadde":    price_tad,
            })

        # 5) build DataFrame
        df = pd.DataFrame(data)
        print(f"[DEBUG] Parsed {len(df)} line(s) out of {n} total")

        if "Invoice date" in df.columns:
            df["Invoice date"] = pd.to_datetime(
                df["Invoice date"], dayfirst=True, errors="coerce"
            ).dt.date

        # 6) sanity-check totals
        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        # 7) validate & return
        self.validate(df)
        return df
