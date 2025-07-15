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
          - order_number   (str)
          - order_id       (uuid or empty)
          - price_wuunder (sum)
        """
        pdf_stream = io.BytesIO(file_bytes)
        data = []
        lines = []

 
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))


        invoice_number = None
        invoice_date   = None
        total_value    = None

 
        for line in lines:
            if "Total" in line and "excl. VAT" in line and "+" in line:
                euro_matches = re.findall(r"€\s?[\d\.,]+", line)
                if euro_matches:
                    raw = euro_matches[0].replace("€", "").replace(".", "").replace(",", ".").strip()
                    try:
                        total_value = float(raw)
                    except ValueError:
                        total_value = None
                break
            if not invoice_number and "Invoice number" in line:
                m = re.search(r"Invoice number*(F-\d{4}-\d{3})", line)
                if m:
                    invoice_number = m.group(1)
                    print("[DEBUG] Parsed invoice number:", invoice_number)
                    
            if not invoice_date and "Issue date" in line:
                m = re.search(r"Issue date*(\d{1,2}\s+\w+\s+\d{4})", line)
                if m:
                    inv_date = m.group(1)
                    print("[DEBUG] Parsed invoice date:", invoice_date)
 
        i = 0
        while i < len(lines):
            line = lines[i].strip().replace("*","")
            print(f"[DEBUG] line:{line}")
            m = re.match(
                r"^(whoppah+\d{3})\s+(\S+)\s+(.*?)\s+(.*?)\s+(.*?)\s+(€[\d]+)$",                                                                                        
                line
            )
            if m:
                order_number, qty, unit_price, vat, price_tot = m.groups()

                price = float(price_tot)

                order_id = ""
                for j in range(1, 5):
                    if i + j < len(lines):
                        u = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                                      lines[i + j])
                        if u:
                            order_id = u.group(0)
                            break

        
              
                data.append({
                    "invoice_number":   invoice_number,
                    "invoice_date":     invoice_date,
                    "order_number":     order_number.lower(),
                    "order_id":         order_id,
                    "qty":             qty,
                    "unit_price":       unit_price,
                    "vat":             vat,
                    "price_tadde":    price,
                })
                i += 1
                continue   
            i += 1
        df = pd.DataFrame(data)
      
        if "invoice_date" in df.columns and df["invoice_date"].dtype == object:
            df["invoice_date"] = pd.to_datetime(
                df["invoice_date"], dayfirst=True, errors="coerce"
            ).dt.date

        if total_value is not None:
            parsed_sum = round(df["price_tadde"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        self.validate(df)
        return df
