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
        lines = []
        with pdfplumber.open(pdf_stream) as pdf:
            for p, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                for ln in text.split("\n"):
                    stripped = ln.strip()
                    if stripped:
                        lines.append(stripped)
        print(f"[DEBUG] Total lines read: {len(lines)}")

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
        whop_re  = re.compile(r"^(whoppah\d{3,})$", re.IGNORECASE)
        price_re = re.compile(
            r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)"
        )
        uuid_re  = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE
        )

        data = []
        current = None

        for idx, ln in enumerate(lines):
            # start a new item when we see a whoppah code
            wm = whop_re.match(ln)
            if wm:
                # flush any in‑progress partial (shouldn't happen)
                if current:
                    print(f"[WARN] dropping incomplete item: {current}")
                current = {
                    "Invoice number": invoice_number or "",
                    "Invoice date":   invoice_date,
                    "order_number":   wm.group(1).lower(),
                    "Order ID":       None,
                    "qty":            None,
                    "unit_price":     None,
                    "vat":            None,
                    "price_tadde":    None,
                }
                print(f"[DEBUG] ← New item started at line {idx}: {current['order_number']}")
                continue

            # if we have an active item and we see a price‑line
            if current:
                pm = price_re.match(ln)
                if pm:
                    # populate price fields
                    current["qty"]          = int(pm.group(1))
                    current["unit_price"]   = float(pm.group(2).replace(",", "."))
                    current["vat"]          = int(pm.group(3))
                    current["price_tadde"]  = float(pm.group(4).replace(",", "."))
                    print(f"[DEBUG]   ↪ price line at {idx}: qty={current['qty']} "
                          f"unit={current['unit_price']} vat={current['vat']} "
                          f"total={current['price_tadde']}")

                    # now look *after* for the UUID
                    found_uuid = False
                    for j in range(1, 6):
                        if idx + j < len(lines):
                            uu = uuid_re.search(lines[idx + j])
                            if uu:
                                current["Order ID"] = uu.group(0)
                                print(f"[DEBUG]   ↪ found UUID at line {idx+j}: {current['Order ID']}")
                                found_uuid = True
                                break

                    if not found_uuid:
                        print(f"[WARN]   ↪ no UUID found for item {current['order_number']}")

                    # finally, only append if we have qty, price & Order ID
                    if current["qty"] is not None and current["price_tadde"] is not None and current["Order ID"]:
                        data.append(current)
                        print(f"[DEBUG]   ✅ Appended item: {current}")
                    else:
                        print(f"[WARN]   ❌ Incomplete item, skipping: {current}")

                    # reset for the next
                    current = None
                    continue

        # 4) build DataFrame
        df = pd.DataFrame(data)
        print(f"[DEBUG] Parsed {len(df)} line‑items from invoice")

        # coerce date
        if "Invoice date" in df.columns:
            df["Invoice date"] = pd.to_datetime(
                df["Invoice date"], dayfirst=True, errors="coerce"
            ).dt.date

        # 5) sanity check total
        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")
        # *** DEBUG DUMP ***
        print("[TADDEParser] final invoice‑DF:")
        print(df.to_string(index=False))
        # 6) validate & return
        self.validate(df)
        return df

