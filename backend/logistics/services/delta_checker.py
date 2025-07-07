#backend/logistics/services/delta_checker.py
import pandas as pd
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

    def evaluate(
        self,
        partner: str,
        df_list: list,
        invoice_bytes: bytes,
        pdf_bytes: bytes | None = None,
        delta_threshold: float = 20.0
    ) -> tuple[bool, bool, pd.DataFrame | None]:
        """
        Compute delta for the given partner using in‐memory file bytes.

        Returns:
            - delta_ok: True if delta_sum <= threshold
            - parsed_ok: True if any invoice rows were parsed
            - df_merged: the merged DataFrame (or None on failure)
        """
        try:
            partner = partner.strip().lower()
            df_order = self.db_service.get_orders_dataframe(partner)

            parser_cls = parser_registry.get(partner)
            if not parser_cls:
                raise ValueError(f"Unsupported partner: {partner}")

            parser = parser_cls()

            # Parse invoice bytes
            if partner == "libero":
                if pdf_bytes is None:
                    raise ValueError("Libero requires both invoice & PDF bytes")
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
                raise NotImplementedError(f"No calculator configured for partner '{partner}'")

            return self._process(df_invoice, calculator.compute, partner, df_list, delta_threshold)

        except Exception as e:
            print(f"❌ Error in DeltaChecker.evaluate: {e}")
            return False, False, None

    def _process(self, df_invoice, compute_fn, partner, df_list, delta_threshold):
        # Run the partner-specific compute()
        df_merged, raw_delta_sum, raw_parsed_flag = compute_fn()

        # If compute() failed
        if df_merged is None:
            return False, False, None

        # Cast to native Python types
        delta_sum   = float(raw_delta_sum)
        parsed_flag = bool(raw_parsed_flag)
        delta_ok    = delta_sum <= float(delta_threshold)

        # Ensure DataFrame columns are native types
        if "Delta" in df_merged.columns:
            df_merged["Delta"] = df_merged["Delta"].astype(float)
        if "Delta_sum" in df_merged.columns:
            df_merged["Delta_sum"] = float(df_merged["Delta_sum"])

        # Append to list for further aggregation or export
        if not df_merged.empty:
            df_merged["Type"]    = "data"
            df_merged["partner"] = partner
            df_list.append(df_merged)
        elif delta_sum == 0 and parsed_flag:
            summary = pd.DataFrame([{
                "Partner":     partner,
                "Delta sum":   delta_sum,
                "Message":     "All prices match perfectly",
                "Type":        "summary"
            }])
            df_list.append(summary)

        # Export to Google Sheets (best-effort)
        try:
            sheet_url = self.spreadsheet_exporter.export(df_merged, partner)
            print(f"✅ Exported to Google Sheets: {sheet_url}")
        except Exception as e:
            print(f"⚠️ Failed to export to Google Sheets: {e}")

        return delta_ok, parsed_flag, df_merged
