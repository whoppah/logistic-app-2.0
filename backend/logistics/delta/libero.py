#backend/logistics/delta/libero.py
from .base import BaseDeltaCalculator
import pandas as pd


class LiberoDeltaCalculator(BaseDeltaCalculator):
    def compute(self):
        df_merged = self.df_invoice.merge(self.df_order, left_on="Order ID", right_on="tracking_id", how="inner")
        df_merged["Delta"] = df_merged["price_libero_logistics"] - df_merged["expected_price"]
        delta_sum = df_merged["Delta"].sum()
        flag = bool(df_merged["price_libero_logistics"].sum())

        df_merged["Delta_sum"] = delta_sum
        df_merged["Partner"] = "libero_logistics"

        return df_merged[["Order ID", "price_libero_logistics", "expected_price", "Delta", "Delta_sum"]], delta_sum, flag
