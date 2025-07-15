# backend/logistics/delta/magic_movers.py
import os
import pandas as pd
import requests
from .base import BaseDeltaCalculator

class MagicMoversDeltaCalculator(BaseDeltaCalculator):

    @staticmethod
    def get_coordinates(postal_code, country):
        """API connection to Google Geocode get coordinates out of postal code."""
        API_KEY = os.getenv("GOOGLE_GEOCODE_API_KEY")
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": postal_code,
            "components": f"country:{country}",
            "key": API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        else:
            print("Error geocoding:", data["status"])
            return None

    @staticmethod
    def get_distance_coords(orig_coords, dest_coords):
        """API connection to Google Maps Distance Matrix to get distance in km."""
        API_KEY = os.getenv("GOOGLE_DISTANCE_API_KEY")
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins':      f"{orig_coords[0]},{orig_coords[1]}",
            'destinations': f"{dest_coords[0]},{dest_coords[1]}",
            'key':          API_KEY,
        }
        resp = requests.get(url, params=params).json()
        elem = resp.get("rows", [{}])[0].get("elements", [{}])[0]
        if elem.get("status") == "OK":
            return elem["distance"]["value"] / 1000.0
        else:
            print("No valid route:", elem.get("status"))
            return 0.0

    def calculate_transport_cost(self, row):
        """Calculate transport cost based on seller/buyer country & distance."""
        sc, bc = row["seller_country"], row["buyer_country"]
        sp, bp = row["seller_post_code"], row["buyer_post_code"]

        sc_coords = self.get_coordinates(sc, sp)
        bc_coords = self.get_coordinates(bc, bp)
        dist = 0.0
        if sc_coords and bc_coords:
            dist = self.get_distance_coords(sc_coords, bc_coords)

        if sc == "NL" and bc == "NL":
            return 70
        if sc == "NL" and bc == "BE":
            return 100
        if sc == "NL" and bc == "DE":
            if dist <= 300:
                return 120
            if dist <= 500:
                return 150
            return 200
        if sc == "NL" and bc == "FR":
            if dist <= 300:
                return 120
            if dist <= 500:
                return 150
            if dist <= 900:
                return 180
            return 240

        return 0  # or None if you prefer

    def calculate_surcharge(self, row):
        """Calculate any special, item‐level surcharges."""
        surcharge = 0
        cat = (row.get("cat_level_2_and_3") or "").lower()
        n   = row.get("number_of_items", 1)
        dims = [row.get(c, 0) for c in ("height", "width", "depth")]
        max_dim = max(dims)

        # example: dining chairs beyond 6
        if "dining-chairs" in cat:
            extra = max(n - 6, 0)
            surcharge += extra * 20

        # …and so on for your other rules…

        # dimension‐based
        if 200 < max_dim <= 240:
            surcharge += 70
        elif 240 < max_dim <= 300:
            surcharge += 150
        elif max_dim > 300:
            print(f"Item {row.get('order_id')} >300 cm, surcharge on request")

        return surcharge

    def calculate_packing_cost(self, row):
        """Calculate packing/wooden crate cost."""
        subtotal = row.get("subtotal_excl_vat", 0)
        items    = row.get("number_of_items", 1)
        dims     = [row.get(c, 0) for c in ("height", "width", "depth")]
        max_dim  = max(dims)

        if subtotal <= 750:
            return 0
        cost = 50
        # crate size tiers
        if max_dim < 100:
            cost += 170
        elif max_dim <= 130:
            cost += 190
        elif max_dim <= 160:
            cost += 220
        elif max_dim <= 200:
            cost += 240
        elif max_dim <= 220:
            cost += 280

        if row.get("is_wooden"):
            cost += items * 20

        return cost

    def compute(self):
        partner_key = "magic_movers"
        df = (
            self.df_invoice
              .merge(
                self.df_order.query(f"external_courier_provider == '{partner_key}'"),
                on="Order ID",
                how="inner"
              )
        )

        # now all of these will be called correctly
        df["transport_cost"] = df.apply(self.calculate_transport_cost, axis=1)
        df["surcharge"]       = df.apply(self.calculate_surcharge, axis=1)
        df["packing_cost"]    = df.apply(self.calculate_packing_cost, axis=1)

        df["price"]           = df["transport_cost"] + df["surcharge"] + df["packing_cost"]
        df["Delta"]           = df[f"price_{partner_key}"] - df["price"]
        delta_sum             = df["Delta"].sum()
        df["Delta_sum"]       = delta_sum

        flag = delta_sum != 0
        cols = [
            "order_creation_date", "Order ID", "weight",
            "buyer_country-seller_country", "cat_level_1_and_2", "cat_level_2_and_3",
            "price", f"price_{partner_key}", "Delta", "Delta_sum",
            "Invoice date", "Invoice number"
        ]
        return df[cols], float(delta_sum), flag
