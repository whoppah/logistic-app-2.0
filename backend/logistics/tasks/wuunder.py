#backend/logistics/tasks/wuunder.py
import pandas as pd
import pdfplumber
import re
import io
from .base_parser import BaseParser
from datetime import datetime


class WuunderParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        pdf_stream = io.BytesIO(file_bytes)
        data = []
        lines = []

        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))

        invoice_number = invoice_date = total_value = None
        for line in lines:
            if "Totaal" in line and "BTW" in line and "+" in line:
                euro_matches = re.findall(r"€\s?[\d\.,]+", line)
                if euro_matches:
                    last_value = euro_matches[0]
                    total_value_str = last_value.replace(".", "").replace(",", ".").replace("€", "").strip()
                    try:
                        total_value = float(total_value_str)
                    except ValueError:
                        total_value = None
                break

        def translate_month(dutch_date: str) -> str:
            try:
                return datetime.strptime(dutch_date, "%d %B %Y").strftime("%Y-%m-%d")
            except ValueError:
                return None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if "Factuurnummer" in line and not invoice_number:
                match = re.search(r"Factuurnummer\s+(\d+)", line)
                if match:
                    invoice_number = match.group(1)

            if "Factuurdatum" in line and not invoice_date:
                match = re.search(r"Factuurdatum:\s*(\d{1,2}\s+\w+\s+\d{4})", line)
                if match:
                    invoice_date = translate_month(match.group(1))

            # Detect shipment row
            match = re.match(r"^(\d{2}-\d{2}-\d{4})\s+(\S+)\s+(.*?)\s+package\s+(.*?)\s+([\d,]+)", line)
            if match:
                shipment_date, order_number, name, carrier, price_str = match.groups()
                price = float(price_str.replace(",", "."))

                # Extract order ID (UUID) from next lines
                order_id = ""
                for j in range(1, 5):
                    if i + j < len(lines):
                        uuid_match = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", lines[i + j])
                        if uuid_match:
                            order_id = uuid_match.group(0)
                            break

                # Fuel price
                fuel_price = None
                for j in range(1, 4):
                    if i + j < len(lines):
                        fuel_line = lines[i + j]
                        if "Fuel" in fuel_line:
                            if "inclusief" in fuel_line.lower():
                                fuel_price = 0.0
                            else:
                                numbers = re.findall(r"[\d]+(?:[\.,]\d+)?", fuel_line)
                                if numbers:
                                    value_str = numbers[-1].replace(",", ".")
                                    try:
                                        fuel_price = float(value_str)
                                    except ValueError:
                                        fuel_price = None
                            break

                # Shipment tags
                context_lines = " ".join(lines[max(0, i-2):i+5]).lower()
                tags = []
                if "additional" in context_lines:
                    tags.append("Additional")
                if "return shipment" in context_lines or "retour" in context_lines:
                    tags.append("Return shipment")
                if "claimprocess started" in context_lines:
                    tags.append("Claim started")
                if "claim paid" in context_lines:
                    tags.append("Claim paid")
                if "claim refused" in context_lines:
                    tags.append("Claim refused")

                # Delivery method
                delivery_method = ""
                for j in range(1, 4):
                    if i + j < len(lines):
                        match = re.search(r"(Retour.*|Pakket op pallet|Drop At Parcelshop|ShopReturn|Standard.*)", lines[i + j])
                        if match:
                            delivery_method = match.group(1)
                            break

                price_total = price + (fuel_price if fuel_price is not None else 0.0)

                row = {
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date,
                    "shipment_date": shipment_date,
                    "order_number": order_number.lower(),
                    "order_id": order_id,
                    "name": name,
                    "carrier": carrier,
                    "price": price,
                    "fuel_price": fuel_price,
                    "price_wuunder": price_total,
                    "shipment_tags": ", ".join(tags),
                    "delivery_method": delivery_method
                }
                data.append(row)
                i += 1
            else:
                i += 1

        df = pd.DataFrame(data)
        df["shipment_date"] = pd.to_datetime(df["shipment_date"], dayfirst=True, errors="coerce")
        df["invoice_date"] = pd.to_datetime(df["invoice_date"], dayfirst=True, errors="coerce")

        # Final validation
        sum_price = round(df["price_wuunder"].sum(), 2)
        if total_value and abs(total_value - sum_price) > 0.01:
            print(f"[WARN] Total mismatch: invoice {total_value} != parsed {sum_price}")
        else:
            print(f"[OK] Total matches: {sum_price}")

        self.validate(df)
        return df
