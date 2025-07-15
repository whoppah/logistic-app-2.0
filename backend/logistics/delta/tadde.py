#backend/logistics/delta/tadde.py
import os
import pandas as pd
import numpy as np
from .base import BaseDeltaCalculator
from django.conf import settings


class TaddeDeltaCalculator(BaseDeltaCalculator):
    def compute(self):
        partner_value = "tadde"
        
        # Merge invoice and order data
        df_merged = self.df_invoice.merge(
            self.df_order.query(f"external_courier_provider == '{partner_value}'"),
            on="Order ID",
            how="inner"
        )
        
        # Load pricing file
        json_path = os.path.join(settings.PRICING_DATA_PATH, "prijslijst_other_partners.json")
        df_price = pd.read_json(json_path)
        df_price["Weightclass"] = df_price["Weightclass"].astype(float).apply(lambda x: format(x, '.2f'))

        # Compute matched prices
        prices = []
        for _, row in df_merged.iterrows():
            category_23 = row.get("cat_level_2_and_3")
            weight = row.get("weight")
            creation_date = row.get("order_creation_date")
            buyer_seller_country = row.get("buyer_country-seller_country")
            matched_price = 0

            change_price_date = pd.Timestamp("2025-02-01")

            for _, price_row in df_price.iterrows():
                if price_row["CMS category"] == category_23 and price_row["Weightclass"] == weight:
                    if creation_date < change_price_date:
                        if f"{buyer_seller_country}-OLD" in price_row:
                            column_key = f"{buyer_seller_country}-OLD-{partner_value}"
                        else:
                            column_key = f"{buyer_seller_country}-{partner_value}"
                    else:
                        column_key = f"{buyer_seller_country}-{partner_value}"
                    matched_price = price_row.get(column_key, matched_price)
                    break
            prices.append(matched_price)

        # Assign computed prices and deltas
        df_merged["price"] = prices
        df_merged["Delta"] = df_merged["price_tadde"] - df_merged["price"]
        delta_sum = df_merged["Delta"].sum()
        flag = df_merged["price"].sum() != 0

        df_merged["Delta_sum"] = delta_sum
        df_merged["Partner"] = partner_value
        print("df_merged sw is :", df_merged)
        # Print any mismatches
        filtered_df = df_merged[df_merged["Delta"] >= 0][
            ["Order ID", "buyer_country-seller_country", "weight", "price", "price_tadde", "Delta", "Delta_sum"]
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
            "price_tadde",
            "Delta",
            "Delta_sum",
            "Invoice date",
            "Invoice number"
        ]
        return df_merged[cols], delta_sum, flag
