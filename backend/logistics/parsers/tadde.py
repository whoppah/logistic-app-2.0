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
        data = []
        pdf_stream = io.BytesIO(file_bytes)
        total_value = None
        invoice_date = invoice_num = None

        # 1) Read metadata
        print("🔍 Starting metadata pass")
        all_lines = []
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                all_lines += text.split("\n")

        for ln in all_lines:
            ln = ln.strip()
            if invoice_num is None:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_num = m.group(1)
                    print(f"[META] Found Invoice number: {invoice_num}")
            if invoice_date is None:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"[META] Found Invoice date: {invoice_date}")
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    raw = m.group(1).replace(",", "")
                    try:
                        total_value = float(raw)
                        print(f"[META] Found Total excl. VAT: {total_value}")
                    except ValueError:
                        print(f"[META] Could not parse total from '{raw}'")
                        total_value = None
            if invoice_num and invoice_date and total_value is not None:
                break

        # 2) Prepare regexes
        whop_re  = re.compile(r"^(whoppah\d{3,})$", re.IGNORECASE)
        uuid_re  = re.compile(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            re.IGNORECASE
        )
        price_re = re.compile(
            r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)"
        )

        # 3) Per-page, per-line extraction
        pdf_stream.seek(0)
        with pdfplumber.open(pdf_stream) as pdf:
            for num_page, page in enumerate(pdf.pages):
                print(f"\n📄 Page {num_page + 1}/{len(pdf.pages)}")
                lines = [l.strip() for l in (page.extract_text() or "").split("\n") if l.strip()]
                next_lines = []
                if num_page + 1 < len(pdf.pages):
                    next_lines = [l.strip() for l in (pdf.pages[num_page+1].extract_text() or "").split("\n") if l.strip()]

                skip_next = False
                for i, ln in enumerate(lines):
                    if skip_next:
                        print(f"[SKIP] Skipping line {i} (was used for UUID)")
                        skip_next = False
                        continue

                    print(f"[LINE {i}] '{ln}'")
                    # 3a) detect whoppah code → start a new record
                    m_wh = whop_re.match(ln)
                    if m_wh:
                        current = {
                            "Invoice number": invoice_num or "",
                            "Invoice date":   invoice_date,
                            "order_number":   m_wh.group(1).lower(),
                            "Order ID":       "",
                            "qty":            None,
                            "unit_price":     None,
                            "vat":            None,
                            "price_tadde":    None
                        }
                        print(f"  ↪️  New item, order_number={current['order_number']}")
                        continue

                    # 3b) detect price line → fill in qty/unit/vat/price
                    pm = price_re.match(ln)
                    if pm:
                        if 'current' not in locals():
                            print(f"  ⚠️  Price line but no current item started")
                            continue
                        current["qty"]         = int(pm.group(1))
                        current["unit_price"]  = float(pm.group(2).replace(",", "."))
                        current["vat"]         = int(pm.group(3))
                        current["price_tadde"] = float(pm.group(4).replace(",", "."))
                        print(f"  ↪️  Parsed price line: qty={current['qty']}, unit_price={current['unit_price']}, vat={current['vat']}, price_tadde={current['price_tadde']}")

                        # 3c) look ahead for UUID
                        found_uuid = False
                        for look in range(1, 4):
                            if i + look < len(lines):
                                uu_line = lines[i + look]
                            else:
                                idx = i + look - len(lines)
                                uu_line = next_lines[idx] if idx < len(next_lines) else ""
                            uu = uuid_re.search(uu_line)
                            if uu:
                                current["Order ID"] = uu.group(0)
                                print(f"  ↪️  Found UUID on line {i+look}: {current['Order ID']}")
                                skip_next = True
                                found_uuid = True
                                break
                        if not found_uuid:
                            print(f"  ⚠️  Could not find UUID for this price block, skipping item")
                            del current
                            continue

                        # 3d) now we have a full record → append and clear
                        data.append(current)
                        print(f"  ✅  Appended item {current}")
                        del current
                        continue

                    # otherwise, nothing to do
                    print(f"  —  no match")

        # 4) Build DataFrame
        df = pd.DataFrame(data)
        if df.empty:
            raise ValueError("No valid rows extracted from Tadde PDF.")

        # coerce types
        df["Invoice date"]   = pd.to_datetime(df["Invoice date"], dayfirst=True, errors="coerce").dt.date
        df["qty"]            = df["qty"].astype(int)
        df["unit_price"]     = df["unit_price"].astype(float)
        df["vat"]            = df["vat"].astype(int)
        df["price_tadde"]    = df["price_tadde"].astype(float)

        # 5) Sanity‐check total
        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total excl. VAT mismatch: reported {total_value} vs parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")
         # *** DEBUG DUMP ***
        print("[TADDEParser] final invoice‑DF:")
        print(df.to_string(index=False))
        
        # 6) Final validate & return
        self.validate(df)
        return df
