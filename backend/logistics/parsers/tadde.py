#backend/logistics/parser/tadde.py
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
          - Invoice number (str)
          - Invoice date   (date)
          - order_number   (the whoppahXXX code)
          - Order ID       (UUID)
          - qty (int), unit_price (float), vat (int), price_tadde (float)
        """
        #Extract all text lines
        pdf_stream = io.BytesIO(file_bytes)
        lines: list[str] = []
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # strip BOM/spaces
                    for ln in text.split("\n"):
                        lines.append(ln.strip())

        #Pull out invoice metadata (number, date, total)
        invoice_number: str | None = None
        invoice_date: date | None   = None
        total_value: float | None   = None

        for ln in lines:
            if not invoice_number:
                m = re.match(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_number = m.group(1)
            if not invoice_date:
                m = re.match(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    raw = m.group(1).replace(".", "").replace(",", ".")
                    try:
                        total_value = float(raw)
                    except ValueError:
                        total_value = None
            # stop once we have everything
            if invoice_number and invoice_date and total_value is not None:
                break

        #Walk lines to capture each “whoppahXXX” block
        data = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            # match the whoppah code
            m = re.match(r"^(whoppah\d{3,})$", ln, flags=re.IGNORECASE)
            if m:
                order_number = m.group(1).lower()
                # look ahead for UUID and qty‑unit‑price line
                order_id = ""
                qty = unit_price = vat_pct = price_tadde = None

                # next few lines
                for j in range(1, 5):
                    if i + j >= len(lines):
                        break
                    nxt = lines[i + j]
                    # UUID
                    uu = re.search(
                        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                        nxt
                    )
                    if uu and not order_id:
                        order_id = uu.group(0)
                    # qty/unit line
                    qm = re.match(
                        r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)",
                        nxt
                    )
                    if qm and qty is None:
                        qty        = int(qm.group(1))
                        unit_price = float(qm.group(2).replace(",", "."))
                        vat_pct    = int(qm.group(3))
                        price_tadde= float(qm.group(4).replace(",", "."))
                        break

                # Only append if we got a price
                if qty is not None and price_tadde is not None:
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
                i += 1
                continue

            i += 1

        #Build DataFrame
        df = pd.DataFrame(data)

        # enforce types / rename
        if "Invoice date" in df:
            df["Invoice date"] = pd.to_datetime(
                df["Invoice date"], dayfirst=True, errors="coerce"
            ).dt.date
        # final total check
        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        #Validation per BaseParser
        self.validate(df)
        return df
