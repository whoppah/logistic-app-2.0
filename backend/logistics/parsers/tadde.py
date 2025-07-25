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
        Parse a multi-page Tadde PDF into invoice-line rows.
        """
        # ─── 1) Read every page and collect lines ─────────────────────────────
        lines_per_page = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                page_lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
                print(f"[DEBUG] Page {page_num}: {len(page_lines)} lines")
                lines_per_page.append(page_lines)

        # ─── 2) Extract metadata from all lines ───────────────────────────────
        all_lines = [ln for pg in lines_per_page for ln in pg]
        invoice_number = invoice_date = total_value = None
        for ln in all_lines:
            if invoice_number is None:
                m = re.search(r"Invoice number\s*(F-\d{4}-\d{3})", ln)
                if m:
                    invoice_number = m.group(1)
                    print(f"[META] Invoice number:    {invoice_number}")
            if invoice_date is None:
                m = re.search(r"Issue date\s*(\d{2}-\d{2}-\d{4})", ln)
                if m:
                    invoice_date = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                    print(f"[META] Invoice date:      {invoice_date}")
            if total_value is None and "Total excl. VAT" in ln:
                m = re.search(r"€\s*([\d\.,]+)", ln)
                if m:
                    total_value = float(m.group(1).replace(",", ""))
                    print(f"[META] Total excl. VAT:   {total_value}")
            if invoice_number and invoice_date and total_value is not None:
                break

        # ─── 3) Compile data from line blocks ─────────────────────────────────
        whop_re  = re.compile(r"^(whoppah\d{3,})$", re.IGNORECASE)
        price_re = re.compile(r"^(\d+)\s+unit\s+€\s*([\d\.,]+)\s+(\d+)\s+%\s+€\s*([\d\.,]+)")
        uuid_re  = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE
        )

        data = []

        for page_idx, lines in enumerate(lines_per_page, start=1):
            i = 0
            while i < len(lines):
                ln = lines[i]
                wm = whop_re.match(ln)
                if not wm:
                    i += 1
                    continue
                order_number = wm.group(1).lower()
                print(f"[PAGE {page_idx}] New item at line {i}: {order_number}")

                lines[i] = ln[len(wm.group(0)):].strip()

                qty = unit_price = vat_pct = price_tad = None
                order_id = None
                price_found_at = uuid_found_at = None

                for offset in range(1, 6):
                    if i + offset < len(lines):
                        line = lines[i + offset]

                        if not order_id:
                            uu = uuid_re.search(line)
                            if uu:
                                order_id = uu.group(0)
                                uuid_found_at = offset

                        if price_tad is None:
                            pm = price_re.match(line)
                            if pm:
                                qty        = int(pm.group(1))
                                unit_price = float(pm.group(2).replace(",", "."))
                                vat_pct    = int(pm.group(3))
                                price_tad  = float(pm.group(4).replace(",", "."))
                                price_found_at = offset

                    if order_id and price_tad is not None:
                        break

                if order_id:
                    print(f"  ↪ uuid at line {i + uuid_found_at}: {order_id}")
                else:
                    print(f"  ⚠️ no UUID found for {order_number}")

                if price_tad is not None:
                    print(f"  ↪ price at line {i + price_found_at}: qty={qty}, total={price_tad}")
                else:
                    print(f"  ⚠️ price missing for {order_number}")

                if qty is not None and order_id:
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
                    i += max(price_found_at or 0, uuid_found_at or 0) + 1
                else:
                    print(f"  ❌ skipping incomplete {order_number}")
                    i += 1

        # ─── 4) Finalize DataFrame ───────────────────────────────────────────
        df = pd.DataFrame(data)
        print(f"\n[DEBUG] total parsed rows: {len(df)}")

        if "Invoice date" in df:
            df["Invoice date"] = pd.to_datetime(df["Invoice date"], dayfirst=True).dt.date

        if total_value is not None:
            s = round(df["price_tadde"].sum(), 2)
            if abs(s - total_value) > 0.01:
                print(f"\n [WARN] total mismatch: reported {total_value} vs parsed {s}")
            else:
                print(f"\n [OK] Total matches: {s}")

        self.validate(df)
        return df
