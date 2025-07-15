# backend/logistics/parsers/wuunder.py
import io
import re
import pandas as pd
import pdfplumber
from datetime import datetime, date
from .base_parser import BaseParser

class WuunderParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        """
        Parse a Wuunder PDF into a DataFrame of shipment rows, extracting:
          - invoice_number (str)
          - invoice_date   (date)
          - shipment_date  (date)
          - order_number   (str)
          - order_id       (uuid or empty)
          - name, carrier, price, fuel_price
          - price_wuunder (sum)
          - shipment_tags, delivery_method
        """
        pdf_stream = io.BytesIO(file_bytes)
        data = []
        lines = []

 
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))
 
        def translate_month(dutch_date: str) -> date | None:
            try:
                 
                dt = datetime.strptime(dutch_date.strip().lower(), "%d %B %Y")
                return dt.date()
            except ValueError:
                return None

        invoice_number = None
        invoice_date   = None
        total_value    = None

 
        for line in lines:
            print(f"[DEBUG] line:{line}")
            if "Totaal" in line and "BTW" in line and "+" in line:
                euro_matches = re.findall(r"€\s?[\d\.,]+", line)
                if euro_matches:
                    raw = euro_matches[0].replace("€", "").replace(".", "").replace(",", ".").strip()
                    try:
                        total_value = float(raw)
                    except ValueError:
                        total_value = None
                break
            if not invoice_number and "Factuurnummer" in line:
                m = re.search(r"Factuurnummer[:\s]+(\d+)", line)
                if m:
                    invoice_number = m.group(1)
                    print("[DEBUG] Parsed invoice number:", invoice_number)
                    
            if not invoice_date and "Factuurdatum" in line:
                m = re.search(r"Factuurdatum[:\s]*(\d{1,2}\s+\w+\s+\d{4})", line, flags=re.IGNORECASE)
                if m:
                    inv_date = translate_month(m.group(1))
                    print("[DEBUG] Parsed inv date:", inv_date)
                    if inv_date:
                        invoice_date = inv_date
                        print("[DEBUG] Parsed invoice date:", invoice_date)
 
        i = 0
        while i < len(lines):
            line = lines[i].strip()
 
            m = re.match(
                r"^(\d{2}-\d{2}-\d{4})\s+(\S+)\s+(.*?)\s+package\s+(.*?)\s+([\d,]+)$",
                line
            )
            if m:
                shipment_str, order_number, name, carrier, price_str = m.groups()
      
                try:
                    shipment_date = datetime.strptime(shipment_str, "%d-%m-%Y").date()
                except ValueError:
                    shipment_date = None

                price = float(price_str.replace(",", "."))

                order_id = ""
                for j in range(1, 5):
                    if i + j < len(lines):
                        u = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                                      lines[i + j])
                        if u:
                            order_id = u.group(0)
                            break

        
                fuel_price = None
                for j in range(1, 4):
                    if i + j < len(lines) and "Fuel" in lines[i + j]:
                        nums = re.findall(r"[\d]+(?:[\,\.]\d+)?", lines[i + j])
                        if nums:
                            try:
                                fuel_price = float(nums[-1].replace(",", "."))
                            except ValueError:
                                fuel_price = None
                        break

          
                context = " ".join(lines[max(0, i - 2): i + 5]).lower()
                tags = []
                if "additional" in context:
                    tags.append("Additional")
                if "retour" in context or "return shipment" in context:
                    tags.append("Return shipment")
                if "claimprocess started" in context:
                    tags.append("Claim started")
                if "claim paid" in context:
                    tags.append("Claim paid")
                if "claim refused" in context:
                    tags.append("Claim refused")

                delivery_method = ""
                for j in range(1, 4):
                    if i + j < len(lines):
                        dm = re.search(r"(Retour.*|Pakket op pallet|Drop At Parcelshop|ShopReturn|Standard.*)",
                                       lines[i + j])
                        if dm:
                            delivery_method = dm.group(1)
                            break

                price_total = price + (fuel_price or 0.0)

                data.append({
                    "invoice_number":   invoice_number,
                    "invoice_date":     invoice_date,
                    "shipment_date":    shipment_date,
                    "order_number":     order_number.lower(),
                    "order_id":         order_id,
                    "name":             name,
                    "carrier":          carrier,
                    "price":            price,
                    "fuel_price":       fuel_price,
                    "price_wuunder":    price_total,
                    "shipment_tags":    ", ".join(tags),
                    "delivery_method":  delivery_method,
                })
                i += 1
                continue   
            i += 1
        df = pd.DataFrame(data)

        if "shipment_date" in df.columns:
            df["shipment_date"] = pd.to_datetime(
                df["shipment_date"], errors="coerce"
            ).dt.date


        if "invoice_date" in df.columns and df["invoice_date"].dtype == object:
            df["invoice_date"] = pd.to_datetime(
                df["invoice_date"], dayfirst=True, errors="coerce"
            ).dt.date

        if total_value is not None:
            parsed_sum = round(df["price_wuunder"].sum(), 2)
            if abs(parsed_sum - total_value) > 0.01:
                print(f"[WARN] Total mismatch: reported {total_value} != parsed {parsed_sum}")
            else:
                print(f"[OK] Total matches: {parsed_sum}")

        self.validate(df)
        return df
