# backend/logistics/delta/libero.py
import pandas as pd
import numpy as np
import os
import itertools

from .base import BaseDeltaCalculator
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
         
        cols = [
            "order_creation_date",
            "Order ID",
            "weight",
            "buyer_country-seller_country",
            "cat_level_1_and_2",
            "cat_level_2_and_3",
            "price",
            "price_libero_logistics",
            "Delta",
            "Delta_sum",
            "Invoice date",
            "Invoice number"
        ]
        return df_merged[cols], delta_sum, flag


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
            "NL10", "NL11", "NL12", "NL13", "NL14", "NL15", "NL16", "NL17", "NL18", "NL19","NL20", "NL21", "NL22", "NL23", "NL24", "NL25", "NL26", "NL27", "NL28", "NL29","NL30", 
            "NL33", "NL34", "NL35", "NL36", "NL37", "NL38", "NL39", "NL40", "NL41", "NL42", 
            "NL48", "NL49", "NL50", "NL51", "NL52", "NL53", 
            "NL54", "NL55", "NL56", "NL57", "NL58", "NL59", 
            "NL65", "NL66", "NL67", "NL68", "NL69", "NL70", "NL71", "NL72", "NL73","NL74", "NL75", "NL76", "NL77", "NL78", "NL79", "NL80", "NL81", "NL82", "NL83","NL84", "NL85", "NL86", "NL87", "NL88", "NL89", "NL90", "NL91", "NL92", "NL93","NL94", "NL95", "NL96", "NL97", "NL98", "NL99",
        ])
        # define all the continuous blocks for NODE
        ranges = [
            range(10000, 11000),   # 10000–10999
            range(12000, 14000),   # 12000–13999
            range(14050, 14090),   # 14050–14089
            range(14109, 14200),   # 14109–14199
            range(14467, 14483),   # 14467–14482
            range(14513, 14514),   # 14513
            range(14974, 14980),   # 14974–14979
            range(20095, 20100),   # 20095–20099
            range(20144, 20150),   # 20144–20149
            range(20457, 20458),   # 20457
            range(20535, 20540),   # 20535–20539
            range(21029, 21030),   # 21029
            range(21031, 21032),   # 21031
            range(21033, 21034),   # 21033
            range(21035, 21036),   # 21035
            range(21047, 21050),   # 21047–21049
            range(21073, 21080),   # 21073–21079
            range(21107, 21110),   # 21107–21109
            range(21129, 21150),   # 21129–21149
            range(21217, 21218),   # 21217
            range(21307, 21308),   # 21307
            range(21435, 21436),   # 21435
            range(21465, 21466),   # 21465
            range(21509, 21510),   # 21509
            range(21629, 21630),   # 21629
            range(22043, 22050),   # 22043–22049
            range(22081, 22090),   # 22081–22089
            range(22111, 22120),   # 22111–22119
            range(22113, 22114),   # 22113
            range(22159, 22160),   # 22159
            range(22175, 22178),   # 22175–22177
            range(22297, 22300),   # 22297–22299
            range(22301, 22399),   # 22301–22398 (merged from many)
            range(22415, 22420),   # 22415–22419
            range(22453, 22460),   # 22453–22459
            range(22523, 22530),   # 22523–22529
            range(22547, 22550),   # 22547–22549
            range(22605, 22610),   # 22605–22609
            range(22761, 22770),   # 22761–22769
            range(22885, 22886),   # 22885
            range(26121, 26136),   # 26121–26135
            range(28195, 28220),   # 28195–28219
            range(28259, 28280),   # 28259–28279
        ]
        
        # all the isolated outliers
        extras = {
            "14513",
            "38000", "38102", "38106", "38114", "38118",
            "39104", "39106", "39108", "39112", "39124", "39128",
            "30159", "30161", "30163", "30167", "30169", "30171", "30173", "30175", "30177",
            "30449", "30451",
        }
        
        # build the final set
        postal_codes_NODE = {
            f"{i:05d}"
            for i in itertools.chain.from_iterable(ranges)
        } | extras

        results = []
        for _, row in df.iterrows():
            matched_price = 0
            category = row["cat_level_2_and_3"]
            #print(f"[DEBUG] categories {category}")
            b_post = row["buyer_post_code"]
            s_post = row["seller_post_code"]
            b_ctry = row["buyer_country"]
            s_ctry = row["seller_country"]
            b_ruhr = b_ctry + b_post[:2]
            s_ruhr = s_ctry + s_post[:2]
        
            # iterate the loaded Germany price DataFrame
            for _, price_row in df_price_de.iterrows():
                #print(f"[DEBUG] Price_row CMS category {price_row.get("CMS category")}")
                if price_row.get("CMS category") == category:
                    if b_ruhr in postal_codes_ruhrNL and s_ruhr in postal_codes_ruhrNL:
                        matched_price = price_row.get("DE", matched_price)
                    elif b_post in postal_codes_NODE or s_post in postal_codes_NODE:
                        matched_price = 190
                    else:
                        print(f"[WARN] no matched_price found. Update postal code NODE ranges ( the buyer_post_code is {b_post} and the seller_post_code is {s_post} ) or the RUHR values (the buyer ruhr is {b_ruhr} and the seller ruhr is {s_ruhr}).")
                        
                    break
                else:
                    print(f"[WARN] no price_row categories found to match with the related CMS-category. Update the price table categories.")
            results.append(matched_price)
        
        return results
