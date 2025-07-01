#backend/logistics/services/delta_evaluator.py
import pandas as pd
from logistics.delta.brenger import BrengerDeltaCalculator
from logistics.delta.wuunder import WuunderDeltaCalculator
from logistics.delta.libero import LiberoDeltaCalculator
from logistics.delta.swdevries import SwdevriesDeltaCalculator
from logistics.parsers import (
    brenger_read_pdf, wuunder_read_pdf,
    libero_logistics_read_xlsx, swdevries_read_xlsx
)
from logistics.services.spreadsheet_exporter import SpreadsheetExporter
from logistics.services.database_service import DatabaseService


class DeltaEvaluator:
    def __init__(self, db_service: DatabaseService = None, exporter: SpreadsheetExporter = None):
        self.db_service = db_service or DatabaseService()
        self.exporter = exporter or SpreadsheetExporter()

    def evaluate(self, partner_value: str, redis_key: str, redis_key_pdf: str = None,
                 delta_threshold: float = 20.0, df_list: list = None) -> tuple[bool, bool, pd.DataFrame | None]:
        """
        Evaluate delta for a given logistics partner.

        Returns:
            - Boolean: True if delta_sum <= delta_threshold
            - Boolean: True if file parsing was successful
            - DataFrame: the merged result
        """
        try:
            partner_value = partner_value.strip().lower()
            df_order = self.db_service.get_orders_dataframe(partner_value=partner_value)
            df_list = df_list or []

            calculator, df_invoice = self._get_calculator(partner_value, redis_key, redis_key_pdf, df_order)
            if calculator is None or df_invoice is None:
                raise ValueError(f"Unsupported or invalid partner data: {partner_value}")

            df_merged, delta_sum, flag = calculator.compute()
            df_merged["Type"] = "data"
            df_merged["partner"] = partner_value
            df_list.append(df_merged)

            url = self.exporter.export(df_merged, partner_value)
            print(f"✅ Exported to spreadsheet: {url}")

            return delta_sum <= delta_threshold, flag, df_merged

        except Exception as e:
            print(f"❌ Error during delta evaluation for '{partner_value}': {e}")
            return False, False, None

    def _get_calculator(self, partner_value: str, redis_key: str, redis_key_pdf: str, df_order: pd.DataFrame):
        """
        Return the correct calculator and df_invoice based on the partner
        """
        if partner_value == "brenger":
            df_invoice = brenger_read_pdf(redis_key)
            return BrengerDeltaCalculator(df_invoice, df_order), df_invoice

        elif partner_value == "wuunder":
            df_invoice = wuunder_read_pdf(redis_key)
            return WuunderDeltaCalculator(df_invoice, df_order), df_invoice

        elif partner_value == "libero_logistics":
            df_invoice = libero_logistics_read_xlsx(redis_key, redis_key_pdf)
            return LiberoDeltaCalculator(df_invoice, df_order), df_invoice

        elif partner_value == "swdevries":
            df_invoice = swdevries_read_xlsx(redis_key)
            return SwdevriesDeltaCalculator(df_invoice, df_order), df_invoice

        return None, None
