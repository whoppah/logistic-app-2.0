# backend/logistics/delta/brenger.py
import os
import pandas as pd
from django.conf import settings


class BrengerDeltaCalculator:
    def __init__(
        self,
        df_invoice: pd.DataFrame,
        df_order: pd.DataFrame,
        price_file: str = None
    ):
        self.df_invoice = df_invoice
        self.df_order   = df_order
        self.price_file = price_file or os.path.join(
            settings.PRICING_DATA_PATH,
            "prijslijst_brenger.json"
        )
        self.df_price = self._load_price_list()

    def _load_price_list(self) -> pd.DataFrame:
        try:
            with open(self.price_file, "r", encoding="utf-8") as f:
                return pd.read_json(f, orient="columns")
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load pricing file: {self.price_file}"
            ) from e

    def compute(self) -> tuple[pd.DataFrame, float, bool]:
        # merge invoice against order/tracking
        df_merged = self.df_invoice.merge(
            self.df_order,
            left_on="id",
            right_on="tracking_id",
            how="inner"
        )
        df_merged["weight"] = df_merged["weight"].astype(float).round(2)

        unmatched_categories = set()
        prices = []
        price_categories = set(self.df_price["CMS category"].unique())

        for _, row in df_merged.iterrows():
            category = row["cat_level_2_and_3"]
            weight   = row["weight"]
            route    = row["buyer_country-seller_country"]

            matched_price = 0
           
            for _, price_row in self.df_price.iterrows():
                if (
                    price_row["CMS category"] == category
                    and price_row["Weightclass"] == weight
                ):
                    matched_price = price_row.get(route, 0)
                    break

           
            if category not in price_categories:
                unmatched_categories.add(category)

            prices.append(matched_price)

        df_merged["price"] = prices
        df_merged["Delta"] = df_merged["price_brenger"] - df_merged["price"]
        delta_sum = df_merged["Delta"].sum()
        flag      = bool(df_merged["price"].sum())

        if unmatched_categories:
            print(
                "[WARN] The following valid CMS categories had no match in the price categories:", unmatched_categories)

        df_merged["Delta_sum"] = delta_sum
        df_merged["Partner"]   = "brenger"

        
        cols = [
            "id",
            "buyer_country-seller_country",
            "cat_level_2_and_3",
            "weight",
            "price",
            "price_brenger",
            "Delta",
            "Delta_sum",
            "Invoice date",
            "Invoice number",
            "Order ID",
        ]
        return df_merged[cols], delta_sum, flag
