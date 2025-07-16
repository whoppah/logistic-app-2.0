#backend/logistics/delta/wuunder.py
from .base import BaseDeltaCalculator
import pandas as pd
import os
import json
import datetime
from django.conf import settings


class WuunderDeltaCalculator(BaseDeltaCalculator):
    def __init__(self, df_invoice: pd.DataFrame, df_order: pd.DataFrame, price_file: str = None):
        super().__init__(df_invoice, df_order)

    def compute(self):
        df_merged= self.df_invoice.merge(self.df_order, left_on= 'order_id', right_on="Order ID", how='inner')
        df_merged["weight"] = df_merged["weight"].astype(float).round(2)
        df_merged["shipping_excl_vat"] = df_merged["shipping_excl_vat"].astype(float)
        df_merged['Delta'] = df_merged['price_wuunder'] - df_merged['shipping_excl_vat']
        df_merged.rename(columns={"invoice_date":"Invoice date","invoice_number":"Invoice number", "shipping_excl_vat":"price"}, inplace=True)
        delta_sum = df_merged['Delta'].sum()
        df_merged['Delta_sum'] =delta_sum
        print("Delta sum is ", delta_sum)
        flag= False if df_merged["price"].sum() == 0 else True
        filtered_df =df_merged.loc[df_merged['Delta']>=0,  ["tracking_id","Order ID" ,"buyer_country-seller_country", "weight", "price_wuunder", "price", "Delta","Delta_sum"]]
        if not filtered_df.empty:
            print("The following rows have wuunder price higher than one expected from shipping_excl_vat \n",filtered_df)

        cols = [
            "order_creation_date",
            "Order ID",
            "weight",
            "buyer_country-seller_country",
            "cat_level_1_and_2",
            "cat_level_2_and_3",
            "price",
            "price_wuunder",
            "Delta",
            "Delta_sum",
            "Invoice date",
            "Invoice number",
            #"fuel_price",
            #"shipment_tags",
            #"delivery_method"
        ]
        return df_merged[cols], delta_sum, flag
        
        
