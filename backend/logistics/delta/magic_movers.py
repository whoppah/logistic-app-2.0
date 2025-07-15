#backend/logistics/delta/magic_movers.py
import os
import pandas as pd
import numpy as np
import requests
from .base import BaseDeltaCalculator
from django.conf import settings


class MagicMoversDeltaCalculator(BaseDeltaCalculator):
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
          # Extract latitude and longitude from the response
          lat = data["results"][0]["geometry"]["location"]["lat"]
          lon = data["results"][0]["geometry"]["location"]["lng"]
          return lat, lon
      else:
          print("Error: ", data["status"])
          return None
    def get_distance_coords(orig_coords, dest_coords):
        """API connection to Google Maps Distance Matrix to get distance in km out of coordinates."""
        API_KEY = "AIzaSyD5FxSi0KHOC1ACI7r8PAXnvxknqTRWvEU"
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': f"{orig_coords[0]},{orig_coords[1]}",
            'destinations': f"{dest_coords[0]},{dest_coords[1]}",
            'key': API_KEY,
        }
        response = requests.get(url, params=params)
        result = response.json()
        elements = result.get("rows", [{}])[0].get("elements", [{}])[0]
        if elements.get("status") == "OK":
            # Safely retrieve the distance value if available
            distance = elements.get("distance", {}).get("value", 0)  # Default to 0 if distance is missing
            distance_km = distance / 1000  # Convert to kilometers
            return distance_km
        else:
            # Handle the case where 'status' is not "OK", such as "ZERO_RESULTS"
            print("No valid route found. Status:", elements.get("status"))
            return 0
    
    def calculate_transport_cost(self,row):
        """Calculate transport cost based on seller and buyer country."""
        seller_country = row["seller_country"]
        buyer_country = row["buyer_country"]
        seller_postal_code = row["seller_post_code"]
        buyer_postal_code = row["buyer_post_code"]
        buyer_coord = self.get_coordinates(seller_postal_code, seller_country) #get coords from Google API connection
        seller_coord = self.get_coordinates(buyer_postal_code, buyer_country)
        distance_km = self.get_distance_coords(buyer_coord,seller_coord) #get distance from Google API connection
        
        if seller_country == "NL" and buyer_country == "NL":
            return 70
        elif seller_country == "NL" and buyer_country == "BE":
            return 100
        elif seller_country == "NL" and buyer_country == "DE":
            if distance_km <= 300:
                return 120
            elif distance_km <= 500:
                return 150
            else:
                return 200
        elif seller_country == "NL" and buyer_country == "FR":
            if distance_km <= 300:
                return 120
            elif distance_km <= 500:
                return 150
            elif distance_km <= 900:
                return 180
            else:
                return 240
        else:
            return None  # For unsupported routes
    
    def calculate_surcharge(row):
        """ calculate surcharges based on heavy items, weight, packing fee."""
        surcharge = 0
        category = row["cat_level_2_and_3"].lower() if pd.notna(row["cat_level_2_and_3"]) else ""
        height, width, depth = row["height"], row["width"], row["depth"]
        max_dim = max(height,width, depth) # Take max sizes 
        number_of_items = row["number_of_items"]
        
        # Surcharge for specific item types over stools, 2-seaters, armchairs, consoles, dining-chairs, double-beds, vases, dining-tables, sideboard, dressing-tables, liquor-cabinets, decorative-objects, shelving-unit, sideboard-cabinet, wall-cabinet, coffee-tables, modular-sofas, bookcases, table-lamps, swivel-chairs, mirrors, side-chairs, filing-cabinets, chest-of-drawers, floor-lights, side-tables, nightstands, desk, frames
        chairs_after2=[ "armchairs", "folding-chairs","rocking-chairs","side-chairs", "swivel-chairs","conference-chairs","office-chairs", "adjustable-recliner-chair"]
    
        if "dining-chairs" in category:
            extra_dining_chairs = max(number_of_items - 6, 0)
            surcharge += extra_dining_chairs * 20  # €20 per extra chair after 6
        
        for chair in chairs_after2:
            if chair in category:
                extra_chairs = max(number_of_items - 2, 0)
                surcharge += extra_chairs * 20  #  €20 per extra chair after 2
    
        if "garden-chairs":
            extra_garden_chairs = max(number_of_items -6,0)
            if extra_garden_chairs !=0:
                if extra_garden_chairs < 3:
                    surcharge += extra_garden_chairs *20 
                elif extra_garden_chairs <4:
                    surcharge += (extra_garden_chairs -1)*20 +40
                else:
                    surcharge += 20+20+40+(extra_garden_chairs-3)*20 # €20 per extra chair after 2, €40 per extra chair nb 3, then €20 per extra chairs
    
        # Surcharge based on item size (heavy items)
        if 200 < max_dim <= 240:
            surcharge += 70
        elif 240 < max_dim <= 300:
            surcharge += 150
        elif max_dim > 300:
            print(f"Item {row['order_id']} has max_size over 300 cm. Surcharge Upon Request")
        return surcharge
    
    def calculate_packing_cost(self,row):
        """ calculate packing cost """
        subtotal = row["subtotal_excl_vat"]
        cardboard_box=row["is_wooden"]
        number_of_items=row["number_of_items"]
        if subtotal <= 750: # No packing cost if total price is below €750
            return 0
        if subtotal > 750:
            surcharge=50
            # Packing costs apply if sizes are not all NaN
            height, width, depth = row["height"], row["width"], row["depth"]
            max_dim = max(height,width, depth) # max size 
            # Wooden crate costs
            if max_dim < 100: #sizes in cm
                surcharge += 170
            elif max_dim <= 130:
                surcharge += 190
            elif max_dim <= 160:
                surcharge += 220
            elif max_dim <= 200:
                surcharge += 240
            elif max_dim <= 220:
                surcharge += 280
            # Additional (cardboard box)
            if cardboard_box:
                surcharge+= number_of_items*20
            return surcharge
    
    def compute(self):
        partner_value = "magic_movers"
        
        # Merge invoice and order data
        df_merged = self.df_invoice.merge(
            self.df_order.query(f"external_courier_provider == '{partner_value}'"),
            on="Order ID",
            how="inner"
        )
        
        df_merged["transport_cost"] = df_merged.apply(self.calculate_transport_cost, axis=1).fillna(0)
        df_merged["surcharge"] = df_merged.apply(self.calculate_surcharge, axis=1).fillna(0)
        df_merged["packing_cost"] = df_merged.apply(self.calculate_packing_cost, axis=1).fillna(0)
        df_merged["price"] = df_merged["transport_cost"] + df_merged["surcharge"] + df_merged["packing_cost"]
        flag= False if df_merged["price"].sum() == 0 else True
        df_merged['Delta'] = df_merged[f'price_{partner_value}'] - df_merged['price']
        delta_sum = df_merged['Delta'].sum()
        df_merged["Delta_sum"]=delta_sum
        print("Delta sum is ", delta_sum)
        df_merged["Delta_sum"]=delta_sum
        df_merged["Partner"] = "magic_movers"
        print("df_merged magic_movers is :", df_merged)
        # Print any mismatches
        filtered_df = df_merged[df_merged["Delta"] >= 0][
            ["Order ID", "buyer_country-seller_country", "weight", "price", "price_magic_movers", "Delta", "Delta_sum"]
        ]
        if not filtered_df.empty:
            print(f"The following rows have {partner_value} price higher than our price\n", filtered_df)

        cols = [
            "order_creation_date",
            "Order ID",
            "weight",
            "buyer_country-seller_country",
            "cat_level_1_and_2",
            "cat_level_2_and_3",
            "price",
            "price_magic_movers",
            "Delta",
            "Delta_sum",
            "Invoice date",
            "Invoice number"
        ]
        return df_merged[cols], delta_sum, flag
