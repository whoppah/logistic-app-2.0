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
            "NL20", "NL21", "NL22", "NL23", "NL24", "NL25", "NL26", "NL27", "NL28", "NL29", 
            "NL30", "NL33", "NL34", "NL35", "NL36", "NL37", "NL38", "NL39", "NL40", 
            "NL41", "NL42", "NL48", "NL49", "NL50", "NL51", "NL52", "NL53", 
            "NL54", "NL55", "NL56", "NL57", "NL58", "NL59", "NL65", "NL66", "NL67", "NL68", "NL69", "NL70", "NL71", "NL72", "NL73", 
            "NL74", "NL75", "NL76", "NL77", "NL78", "NL79", "NL80", "NL81", "NL82", "NL83", 
            "NL84", "NL85", "NL86", "NL87", "NL88", "NL89", "NL90", "NL91", "NL92", "NL93", 
            "NL94", "NL95", "NL96", "NL97", "NL98", "NL99"])
        # define all the continuous blocks for NODE
        ranges = [
            range(10000, 11000),   # 10000–10999
            range(12000, 14000),   # 12000–13999
            range(14050, 14090),   # 14050–14089
            range(14109, 14193),   # 14109–14192
            range(14467, 14483),   # 14467–14482
            range(14513, 14514),   # 14513
            range(14974, 14980),   # 14974–14979
        ]
        
        # all the isolated outliers
        extras = {
            "38000","38102","38106","38114","38118",
            "39104","39106","39108","39112","39124","39128",
            "30159","30161","30163","30167","30169","30171","30173","30175","30177",
            "30449","30451",
            "21047","21049","21073","21074","21075","21076","21077","21078","21079",
            "21107","21108","21109","21129","21130","21131","21132","21133","21134",
            "21135","21136","21137","21138","21139","21140","21141","21142","21143",
            "21144","21145","21146","21147","21148","21149",
            "20457","20535","20537","20539",
            "21217","21307","21435","21465","21509","21629",
            "22043","22044","22045","22046","22047","22048","22049",
            "22081","22082","22083","22084","22085","22086","22087","22088","22089",
            "22113","22111","22115","22117","22119","22159","22175","22176","22177",
            "22297","22298","22299",
            "22301","22302","22303","22304","22305","22306","22307","22308","22309",
            "22310","22311","22312","22313","22314","22315","22316","22317","22318",
            "22319","22320","22321","22322","22323","22324","22325","22326","22327",
            "22328","22329","22330","22331","22332","22333","22334","22335","22336",
            "22337","22338","22339","22340","22341","22342","22343","22344","22345",
            "22346","22347","22348","22349","22350","22351","22352","22353","22354",
            "22355","22356","22357","22358","22359","22360","22361","22362","22363",
            "22364","22365","22366","22367","22368","22369","22370","22371","22372",
            "22373","22374","22375","22376","22377","22378","22379","22380","22381",
            "22382","22383","22384","22385","22386","22387","22388","22389","22390",
            "22391","22392","22393","22394","22395","22396","22397",
            "22415","22416","22417","22418","22419","22453","22454","22455","22456",
            "22457","22458","22459","22523","22524","22525","22526","22527","22528",
            "22529","22547","22548","22549","22605","22606","22607","22608","22609",
            "22761","22762","22763","22764","22765","22766","22767","22768","22769",
            "22885",
            "28195","28196","28197","28198","28199","28200","28201","28202","28203",
            "28204","28205","28206","28207","28208","28209","28210","28211","28212",
            "28213","28214","28215","28216","28217","28218","28219","28259","28260",
            "28261","28262","28263","28264","28265","28266","28267","28268","28269",
            "28270","28271","28272","28273","28274","28275","28276","28277","28278",
            "28279",
            "26121","26122","26123","26124","26125","26126","26127","26128","26129",
            "26130","26131","26132","26133","26134","26135"
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
