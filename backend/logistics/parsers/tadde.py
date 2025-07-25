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
        Parse a Tadde PDF (possibly multi-page) into invoice-line rows.
        """
        # 1) Open PDF and process page-by-page
        lines_per_page = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                page_lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
                print(f"[DEBUG] Page {page_num}: {len(page_lines)} lines")
                lines_per_page.append(page_lines)

        # 2) Flatten just enough to find invoice metadata (we assume it’s only on page 1)
        all_lines = lines_per_page[0]
        invoice_number = invoice_date = total_value = None
        for ln in all_lines:
            if invoice_number is None:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_number = m.group(1)
                    print(f"[META] Invoice number: {invoice_number}")
            if invoice_date is None:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"[META] Invoice date:   {invoice_date}")
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    total_value = float(m.group(1).replace(",", ""))
                    print(f"[META] Total excl. VAT: {total_value}")
            if invoice_number and invoice_date and total_value is not None:
                break

        # 3) Prepare our regexes
        whop_re  = re.compile(r"^(whoppah\d{3,})$", re.IGNORECASE)
        price_re = re.compile(
            r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)"
        )
        uuid_re  = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE
        )

        data = []

        # 4) Now parse each page separately
        for page_idx, lines in enumerate(lines_per_page, start=1):
            print(f"\n[DEBUG] — parsing page {page_idx}")
            i = 0
            while i < len(lines):
                ln = lines[i]
                # Start on whoppah code
                wm = whop_re.match(ln)
                if wm:
                    order_number = wm.group(1).lower()
                    print(f"[PAGE {page_idx}] New item at line {i}: {order_number}")

                    # strip it to avoid re-matching
                    ln_after = ln[len(wm.group(0)):].strip()
                    lines[i] = ln_after

                    # Next line should be price
                    if i+1 < len(lines):
                        pm = price_re.match(lines[i+1])
                        if pm:
                            qty        = int(pm.group(1))
                            unit_price = float(pm.group(2).replace(",", "."))
                            vat_pct    = int(pm.group(3))
                            price_tad  = float(pm.group(4).replace(",", "."))
                            print(f"  ↪ price on line {i+1}: qty={qty}, total={price_tad}")

                            # Now UUID in lines i+2…i+6
                            order_id = None
                            for j in range(2, 7):
                                if i+j < len(lines):
                                    uu = uuid_re.search(lines[i+j])
                                    if uu:
                                        order_id = uu.group(0)
                                        print(f"  ↪ uuid at line {i+j}: {order_id}")
                                        break
                            if not order_id:
                                print(f"  ⚠️ no UUID found for {order_number}")

                            # Append if complete
                            if order_id:
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
                                print(f"  ✅ appended {order_number}")
                                # Skip past the block
                                i += 1 + 1 + (j if order_id else 1)
                                continue
                            else:
                                print(f"  ❌ skipping incomplete {order_number}")
                        else:
                            print(f"  ⚠️ price‑line missing after {order_number}")
                    i += 1
                    continue

                i += 1

        # 5) Build DataFrame
        df = pd.DataFrame(data)
        print(f"\n[DEBUG] total parsed rows: {len(df)}")

        # 6) Coerce date & sanity‐check
        if "Invoice date" in df:
            df["Invoice date"] = pd.to_datetime(df["Invoice date"], dayfirst=True).dt.date

        if total_value is not None:
            s = round(df["price_tadde"].sum(), 2)
            if abs(s - total_value) > 0.01:
                print(f"[WARN] total mismatch: reported {total_value} vs parsed {s}")
            else:
                print(f"[OK] Total matches: {s}")
        # *** DEBUG DUMP ***
        print("[TADDEParser] final invoice‑DF:")
        print(df.to_string(index=False))
        # 7) Validate & return
        self.validate(df)
        return df

