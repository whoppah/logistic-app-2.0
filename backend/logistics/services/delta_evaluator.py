#backend/logistics/services/delta_evaluator.py
import pandas as pd
from logistics.delta.brenger import BrengerDeltaCalculator
from logistics.delta.wuunder import WuunderDeltaCalculator
from logistics.delta.libero import LiberoDeltaCalculator
from logistics.delta.swdevries import SwdevriesDeltaCalculator
from logistics.parsers import (
    brenger_read_pdf, wuunder_read_pdf,
    libero_logistics_read_xlsx, libero_logistics_read_pdf,
    swdevries_read_xlsx
)
from logistics.export import export_to_spreadsheet
from logistics.db import get_df_from_query_db


def evaluate_delta_from_files(
    partner_value: str,
    redis_key: str,
    redis_key_pdf: str = None,
    delta_threshold: float = 20,
    df_list: list = None
) -> tuple[bool, bool, pd.DataFrame | None]:
    """
    Evaluate delta for a given logistics partner using uploaded file in Redis.

    Returns:
        - True if delta is within threshold
        - True if parsing was successful
        - Final DataFrame with delta computation
    """
    try:
        partner_value = partner_value.strip().lower()
        df_order = get_df_from_query_db(partner_value=partner_value)
        df_list = df_list or []

        calculator = None
        df_invoice = None

        if partner_value == "brenger":
            df_invoice = brenger_read_pdf(redis_key)
            calculator = BrengerDeltaCalculator(df_invoice, df_order)

        elif partner_value == "wuunder":
            df_invoice = wuunder_read_pdf(redis_key)
            calculator = WuunderDeltaCalculator(df_invoice, df_order)

        elif partner_value == "libero_logistics":
            df_invoice = libero_logistics_read_xlsx(redis_key, redis_key_pdf)
            calculator = LiberoDeltaCalculator(df_invoice, df_order)

        elif partner_value == "swdevries":
            df_invoice = swdevries_read_xlsx(redis_key)
            calculator = SwdevriesDeltaCalculator(df_invoice, df_order)

        else:
            raise ValueError(f"Unsupported logistics partner: {partner_value}")

        df_merged, delta_sum, parsed_flag = calculator.compute()
        df_merged["Type"] = "data"
        df_merged["partner"] = partner_value
        df_list.append(df_merged)

        url = export_to_spreadsheet(df_merged, partner_value)
        print(f"✅ Spreadsheet exported: {url}")

        return delta_sum <= delta_threshold, parsed_flag, df_merged

    except Exception as e:
        print(f"❌ Error evaluating delta: {e}")
        return False, False, None
