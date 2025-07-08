# backend/logistics/delta/libero.py
from .base import BaseDeltaCalculator
import pandas as pd
import numpy as np
import os
from django.conf import settings


class LiberoDeltaCalculator(BaseDeltaCalculator):
    def compute(self):
        df_merged = self.df_invoice.merge(
            self.df_order.query("external_courier_provider == 'libero_logistics'"),
            on="Order ID", how="inner"
        )

        # format weight
        df_merged["weight"] = (
            df_merged["weight"]
            .astype(float)
            .apply(lambda x: format(x, ".2f"))
        )

        # load base price list
        base_price_path = os.path.join(
            settings.PRICING_DATA_PATH,
            "prijslijst_other_partners.json"
        )
        df_price = pd.read_json(base_price_path)
        df_price["Weightclass"] = (
            df_price["Weightclass"]
            .astype(float)
            .apply(lambda x: format(x, ".2f"))
        )

        # compute matched prices from base list
        prices = []
        change_price_date = pd.Timestamp("2025-02-01")
        for _, row in df_merged.iterrows():
            matched_price = 0
            for _, p in df_price.iterrows():
                if (
                    p["CMS category"] == row["cat_level_2_and_3"]
                    and p["Weightclass"] == row["weight"]
                ):
                    key_base = row["buyer_country-seller_country"]
                    if row["order_creation_date"] < change_price_date:
                        key = f"{key_base}-OLD"
                    else:
                        key = f"{key_base}-libero_logistics"
                    matched_price = p.get(key, 0)
                    break
            prices.append(matched_price)
        df_merged["price"] = prices

        # apply Germany fallback where needed
        has_de = df_merged[["buyer_country", "seller_country"]].isin(["DE"]).any(axis=1).any()
        if has_de:
            df_merged["price_de"] = self._get_germany_prices(df_merged)
            df_merged["price"] = np.where(
                df_merged["price"] != 0,
                df_merged["price"],
                df_merged["price_de"],
            )

        # compute delta
        df_merged["Delta"] = df_merged["price_libero_logistics"] - df_merged["price"]
        delta_sum = df_merged["Delta"].sum()
        flag = bool(df_merged["price"].sum())

        df_merged["Delta_sum"] = delta_sum
        df_merged["Partner"] = "libero_logistics"

        return (
            df_merged[
                [
                    "Order ID",
                    "buyer_country-seller_country",
                    "weight",
                    "price",
                    "price_libero_logistics",
                    "Delta",
                    "Delta_sum",
                ]
            ],
            delta_sum,
            flag,
        )

    def _get_germany_prices(self, df):
        """Compute fallback prices for DE/NL postal codes from a dedicated JSON."""

        # 1) Load the Germany-specific JSON file
        path = os.path.join(
            settings.PRICING_DATA_PATH,
            "germany_libero_logistic.json"
        )
        try:
            df_price_de = pd.read_json(path)
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load Germany fallback prices from {path}"
            ) from e

        postal_codes_ruhrNL = set([
            "DE40", "DE41", "DE42", "DE44", "DE45", "DE46", "DE47", "DE50",
            "NL10", "NL11", "NL12", "NL13", "NL14", "NL15", "NL16", "NL17", "NL18", "NL19",
        ])
        postal_codes_NODE = set([str(i).zfill(5) for i in range(10000, 12700)] + ["10999"])

        results = []
        for _, row in df.iterrows():
            matched_price = 0
            category = row["cat_level_2_and_3"]
            b_post = row["buyer_post_code"]
            s_post = row["seller_post_code"]
            b_ctry = row["buyer_country"]
            s_ctry = row["seller_country"]

            b_ruhr = b_ctry + b_post[:2]
            s_ruhr = s_ctry + s_post[:2]

            # 2) Iterate the loaded Germany price DataFrame
            for _, price_row in df_price_de.iterrows():
                if price_row.get("CMS category") == category:
                    if b_ruhr in postal_codes_ruhrNL and s_ruhr in postal_codes_ruhrNL:
                        matched_price = price_row.get("DE", matched_price)
                    elif b_post in postal_codes_NODE or s_post in postal_codes_NODE:
                        matched_price = 190
                    break

            results.append(matched_price)

        return results
