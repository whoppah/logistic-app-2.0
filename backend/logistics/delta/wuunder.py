#backend/logistics/delta/wuunder.py
from .base import BaseDeltaCalculator
import pandas as pd
import os
import json
from django.config import settings


class WuunderDeltaCalculator(BaseDeltaCalculator):
    def __init__(self, df_invoice: pd.DataFrame, df_order: pd.DataFrame, price_file: str = None):
        super().__init__(df_invoice, df_order)
        self.price_file = price_file or os.path.join(settings.PRICING_DATA_PATH, "prijslijst_wuunder.json")
        self.df_price = self._load_price_list()

    def _load_price_list(self) -> pd.DataFrame:
        with open(self.price_file, "r", encoding="utf-8") as f:
            return pd.read_json(f, orient="columns")

    def compute(self):
        df_merged = self.df_invoice.merge(self.df_order, left_on="order_number", right_on="tracking_id", how="inner")
        df_merged["weight"] = df_merged["weight"].astype(float).round(2)
        prices = []

        for _, row in df_merged.iterrows():
            matched_price = 0
            for _, price_row in self.df_price.iterrows():
                if price_row["Weightclass"] == row["weight"] and price_row["CMS category"] == row["cat_level_2_and_3"]:
                    matched_price = price_row.get(row["buyer_country-seller_country"], 0)
                    break
            prices.append(matched_price)

        df_merged["price"] = prices
        df_merged["Delta"] = df_merged["price_wuunder"] - df_merged["price"]
        delta_sum = df_merged["Delta"].sum()
        flag = bool(df_merged["price"].sum())

        df_merged["Delta_sum"] = delta_sum
        df_merged["Partner"] = "wuunder"

        return df_merged[["order_number", "price", "price_wuunder", "Delta", "Delta_sum"]], delta_sum, flag
