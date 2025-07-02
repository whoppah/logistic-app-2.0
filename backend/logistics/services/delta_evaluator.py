#backend/logistics/services/delta_evaluator.py
import os
import pandas as pd
from django.conf import settings

from logistics.delta.brenger import BrengerDeltaCalculator
from logistics.delta.wuunder import WuunderDeltaCalculator
from logistics.delta.libero import LiberoDeltaCalculator
from logistics.delta.swdevries import SwdevriesDeltaCalculator

from logistics.parsers.registry import parser_registry
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
        Return the correct calculator and parsed invoice dataframe
        """
        parser_cls = parser_registry.get(partner_value)
        if not parser_cls:
            print(f"❌ No parser registered for partner: {partner_value}")
            return None, None

        parser = parser_cls()

        try:
            if partner_value == "libero":
                if not redis_key_pdf:
                    raise ValueError("Missing PDF metadata file for Libero.")
                context = {"pdf_bytes": self._load_file_bytes(redis_key_pdf)}
                df_invoice = parser.parse(self._load_file_bytes(redis_key), context=context)
                return LiberoDeltaCalculator(df_invoice, df_order), df_invoice

            elif partner_value == "swdevries":
                df_invoice = parser.parse(self._load_file_bytes(redis_key))
                return SwdevriesDeltaCalculator(df_invoice, df_order), df_invoice

            elif partner_value == "wuunder":
                df_invoice = parser.parse(self._load_file_bytes(redis_key))
                return WuunderDeltaCalculator(df_invoice, df_order), df_invoice

            elif partner_value == "brenger":
                df_invoice = parser.parse(self._load_file_bytes(redis_key))
                return BrengerDeltaCalculator(df_invoice, df_order), df_invoice

        except Exception as e:
            print(f"❌ Failed to parse file or initialize calculator for {partner_value}: {e}")
            return None, None

        return None, None

    def _load_file_bytes(self, redis_key: str) -> bytes:
        """
        Load the file content for a given redis_key from disk.
        Tries both .pdf and .xlsx extensions.
        """
        base_path = os.path.join(settings.BASE_DIR, "backend", "logistics", "slack")
        pdf_path = os.path.join(base_path, f"{redis_key}.pdf")
        xlsx_path = os.path.join(base_path, f"{redis_key}.xlsx")

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
        elif os.path.exists(xlsx_path):
            with open(xlsx_path, "rb") as f:
                return f.read()
        else:
            raise FileNotFoundError(f"Could not find file for redis key: {redis_key}")
