#backend/logistics/parsers/brenger.py
import pandas as pd
import pdfplumber
import re
import io
from .base_parser import BaseParser


class BrengerParser(BaseParser):
    def parse(self, file_bytes: bytes) -> pd.DataFrame:
        data = []
        pdf_stream = io.BytesIO(file_bytes)
        total_value = None
        invoice_date, invoice_num = "", ""
        start_extraction = False
        skip_line = False

        with pdfplumber.open(pdf_stream) as pdf:
            for num_page, page in enumerate(pdf.pages):
                text = page.extract_text()
                text_next = pdf.pages[num_page + 1].extract_text() if num_page + 1 < len(pdf.pages) else ""

                if not text:
                    continue

                lines = text.split("\n")
                lines_next = text_next.split("\n") if text_next else []

                columns_value = None
                for i, line in enumerate(lines):
                    line = line.strip()
                    line = re.sub(r"[\u2013\u2014\u2212]", "-", line)

                    # Invoice metadata
                    if "Factuurdatum" in line:
                        match = re.match(r"Factuurdatum:\s*(\d{4}-\d{2}-\d{2})", line)
                        if match:
                            invoice_date = match.group(1)

                    if "Factuurnummer" in line:
                        match = re.match(r"Factuurnummer:\s*(\w+)", line)
                        if match:
                            invoice_num = match.group(1)

                    if "BTW (21%):" in line:
                        start_extraction = False
                        continue

                    if "TOTAAL:" in line:
                        total_match = re.search(r"\u20ac\s*([\d,.]+)", line)
                        if total_match:
                            total_value = total_match.group(1)
                        break

                    if skip_line:
                        skip_line = False
                        continue

                    is_canceled = ". Cancelled." in line
                    line = line.replace(". Cancelled.", "").strip()

                    # Look ahead
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    next_next_line = lines[i + 2].strip() if i + 2 < len(lines) else (lines_next[1].strip() if len(lines_next) > 1 else "")

                    # Start of entry
                    id_match = re.match(r"^(\w{6})\s([\d-]+: .*)", line)
                    if id_match:
                        if columns_value:
                            data.append(columns_value)

                        columns_value = {
                            "Invoice date": invoice_date,
                            "Invoice number": invoice_num,
                            "id": id_match.group(1),
                            "date": "",
                            "pickup_city": "",
                            "dropoff_city": "",
                            "name_pickup": "",
                            "name_dropoff": "",
                            "status": "Cancelled" if is_canceled else "Active",
                            "ordernummer": "",
                            "bedrag_incl_btw": "",
                            "bedrag": ""
                        }
                        line = re.sub(r"^\w{6}\s*", "", line)

                    # Prices
                    bedrag_match = re.search(r"\u20ac\s*([\d,.]+)\s*\u20ac\s*([\d,.]+)", line)
                    if bedrag_match and columns_value:
                        columns_value["bedrag_incl_btw"] = bedrag_match.group(1)
                        columns_value["bedrag"] = bedrag_match.group(2)
                        line = re.sub(r"\u20ac\s*[\d,.]+\s*\u20ac\s*[\d,.]+", "", line).strip()

                    # Trip matching
                    if columns_value:
                        trip_line = self._combine_trip_line(line, next_line, next_next_line)
                        self._extract_trip_details(trip_line, columns_value, disjoint_fallback=(next_line, next_next_line))

                    if "Ordernummer:" in line and columns_value:
                        match = re.match(r"Ordernummer:\s*(\w+)?", line)
                        if match and match.group(1):
                            columns_value["ordernummer"] = match.group(1)

                if columns_value:
                    data.append(columns_value)

        df = pd.DataFrame(data)
        if df.empty:
            raise ValueError("No valid rows extracted from Brenger PDF.")

        # Cleanup and post-processing
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["Invoice date"] = pd.to_datetime(df["Invoice date"], errors="coerce")
        df["bedrag"] = df["bedrag"].str.replace(",", ".").astype(float)
        df["bedrag_incl_btw"] = df["bedrag_incl_btw"].str.replace(",", ".").astype(float)
        df["id"] = df["id"].str.lower()

        df.rename(columns={
            "bedrag": "price_brenger",
            "bedrag_incl_btw": "price_brenger_incl_btw"
        }, inplace=True)

        # Total check
        if total_value:
            total_float = float(total_value.replace(".", "").replace(",", "."))
            sum_check = round(df["price_brenger_incl_btw"].sum(), 2)
            if abs(total_float - sum_check) > 0.01:
                print(f"[WARN] Total mismatch: Invoice says {total_float}, parsed sum is {sum_check}")
            else:
                print(f"[OK] Total matches: {sum_check}")

        self.validate(df)
        return df

    def _combine_trip_line(self, line, next_line, next_next_line):
        if "(" in line and ")" not in line and next_line:
            return line + " " + next_line
        return line

    def _extract_trip_details(self, line, col, disjoint_fallback=("", "")):
        city_pattern = r"([\w\s\-'/\.]+?)"
        m1 = re.match(rf"(\d{{4}}-\d{{2}}-\d{{2}}):\s*{city_pattern}\s*-\s*{city_pattern}\s*\((.*?)\)", line)
        m2 = re.match(rf"(\d{{4}}-\d{{2}}-\d{{2}}):\s*{city_pattern}\s*\((.*?)\)\s*-\s*{city_pattern}\s*\((.*?)\)", line)

        if m2:
            col["date"] = m2.group(1)
            col["pickup_city"] = m2.group(2).strip()
            col["name_pickup"] = m2.group(3).strip()
            col["dropoff_city"] = m2.group(4).strip()
            col["name_dropoff"] = m2.group(5).strip()
        elif m1:
            col["date"] = m1.group(1)
            col["pickup_city"] = m1.group(2).strip()
            col["dropoff_city"] = m1.group(3).strip()
            col["name_pickup"] = m1.group(4).strip()
            col["name_dropoff"] = m1.group(4).strip()
        else:
            col["date"] = "invalid"
            col["pickup_city"] = "error"
            col["dropoff_city"] = "error"
            col["name_pickup"] = "error"
            col["name_dropoff"] = "error"
