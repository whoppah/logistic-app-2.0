#backend/logistics/services/delta_checker.py
import pandas as pd
import redis
from django.conf import settings

from logistics.parsers.registry import parser_registry
from logistics.services.spreadsheet_exporter import SpreadsheetExporter
from logistics.services.database_service import DatabaseService
from logistics.delta.brenger import BrengerDeltaCalculator
from logistics.delta.wuunder import WuunderDeltaCalculator
from logistics.delta.libero import LiberoDeltaCalculator
from logistics.delta.swdevries import SwdevriesDeltaCalculator


class DeltaChecker:
    def __init__(self, db_service=None, spreadsheet_exporter=None):
        self.db_service = db_service or DatabaseService()
        self.spreadsheet_exporter = spreadsheet_exporter or SpreadsheetExporter()
        # initialize Redis client once
        self.redis = redis.from_url(settings.REDIS_URL)

    def evaluate(
        self,
        partner: str,
        redis_key: str,
        df_list: list,
        redis_key_pdf: str = "",
        delta_threshold: float = 20.0
    ) -> tuple[bool, bool, pd.DataFrame | None]:
        """
        Returns (delta_ok: bool, parsed_success: bool, df_merged or None)
        """
        try:
            partner = partner.strip().lower()
            df_order = self.db_service.get_orders_dataframe(partner)

            parser_cls = parser_registry.get(partner)
            if not parser_cls:
                print(f"❌ Unsupported partner: {partner}")
                return False, False, None

            parser = parser_cls()

            # Load invoice bytes from Redis
            invoice_bytes = self._load_file_bytes(redis_key)
            if partner == "libero":
                if not redis_key_pdf:
                    raise ValueError("Missing PDF metadata file for Libero.")
                pdf_bytes = self._load_file_bytes(redis_key_pdf)
                # Libero parser needs both excel and pdf bytes
                df_invoice = parser.parse(invoice_bytes, context={"pdf_bytes": pdf_bytes})
                calculator = LiberoDeltaCalculator(df_invoice, df_order)

            elif partner == "swdevries":
                df_invoice = parser.parse(invoice_bytes)
                calculator = SwdevriesDeltaCalculator(df_invoice, df_order)

            elif partner == "wuunder":
                df_invoice = parser.parse(invoice_bytes)
                calculator = WuunderDeltaCalculator(df_invoice, df_order)

            elif partner == "brenger":
                df_invoice = parser.parse(invoice_bytes)
                calculator = BrengerDeltaCalculator(df_invoice, df_order)

            else:
                raise NotImplementedError(f"No calculator configured for partner: {partner}")

            return self._process(df_invoice, calculator.compute, partner, df_list, delta_threshold)

        except Exception as e:
            print(f"❌ Error in DeltaChecker.evaluate: {e}")
            return False, False, None

    def _process(self, df_invoice, compute_fn, partner, df_list, delta_threshold):
        df_merged, delta_sum, flag = compute_fn()

        if not df_merged.empty:
            df_merged["Type"] = "data"
            df_merged["partner"] = partner
            df_list.append(df_merged)
        elif delta_sum == 0 and flag:
            summary = pd.DataFrame([{
                "Partner": partner,
                "Delta sum": delta_sum,
                "Message": "All prices match perfectly",
                "Type": "summary"
            }])
            df_list.append(summary)

        try:
            url = self.spreadsheet_exporter.export(df_merged, partner)
            print(f"✅ Exported to Google Sheets: {url}")
        except Exception as e:
            print(f"⚠️ Failed to export to Google Sheets: {e}")

        return delta_sum <= delta_threshold, flag, df_merged

    def _load_file_bytes(self, redis_key: str) -> bytes:
        """
        Fetch file bytes from Redis under key "upload:<redis_key>".
        Raises FileNotFoundError if missing.
        """
        redis_redis_key = f"upload:{redis_key}"
        data = self.redis.get(redis_redis_key)
        if not data:
            raise FileNotFoundError(f"No file bytes found in Redis for key: {redis_redis_key}")
        return data
