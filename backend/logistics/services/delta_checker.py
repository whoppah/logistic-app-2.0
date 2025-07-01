#backend/logistics/services/delta_checker.py
# backend/logistics/services/delta_checker.py

import pandas as pd
from logistics.services.spreadsheet_exporter import SpreadsheetExporter
from logistics.services.database_service import DatabaseService
from logistics.extraction.parsers import (
    brenger_read_pdf, wuunder_read_pdf,
    swdevries_read_xlsx, libero_logistics_read_xlsx,
    transpoksi_read_pdf, magic_movers_read_xlsx
)
from logistics.processing.delta import (
    compute_delta_brenger, compute_delta_wuunder,
    compute_delta_other_partners, compute_delta_magic_movers
)


class DeltaChecker:
    def __init__(self, db_service=None, spreadsheet_exporter=None):
        self.db_service = db_service or DatabaseService()
        self.spreadsheet_exporter = spreadsheet_exporter or SpreadsheetExporter()

    def evaluate(
        self,
        partner: str,
        redis_key: str,
        df_list: list,
        redis_key_pdf: str = "",
        file_name: str = "",
        file_name_pdf: str = "",
        delta_threshold: float = 20.0
    ) -> tuple[bool, bool]:
        try:
            partner = partner.strip().lower()
            df_order = self.db_service.get_orders_dataframe(partner)

            handler_map = {
                "brenger": lambda: self._process(
                    brenger_read_pdf(redis_key),
                    lambda df: compute_delta_brenger(df, df_order),
                    partner,
                    df_list,
                    delta_threshold
                ),
                "wuunder": lambda: self._process(
                    wuunder_read_pdf(redis_key),
                    lambda df: compute_delta_wuunder(df, df_order),
                    partner,
                    df_list,
                    delta_threshold
                ),
                "libero_logistics": lambda: self._process(
                    libero_logistics_read_xlsx(redis_key, redis_key_pdf),
                    lambda df: compute_delta_other_partners(df, df_order, partner),
                    partner,
                    df_list,
                    delta_threshold
                ),
                "swdevries": lambda: self._process(
                    swdevries_read_xlsx(redis_key),
                    lambda df: compute_delta_other_partners(df, df_order, partner),
                    partner,
                    df_list,
                    delta_threshold
                ),
                "transpoksi": lambda: self._process(
                    transpoksi_read_pdf(redis_key),
                    lambda df: compute_delta_other_partners(df, df_order, partner),
                    partner,
                    df_list,
                    delta_threshold
                ),
                "magic_movers": lambda: self._process(
                    magic_movers_read_xlsx(invoice_value=None, date_value=None, redis_key=redis_key),
                    lambda df: compute_delta_magic_movers(df, df_order, partner),
                    partner,
                    df_list,
                    delta_threshold
                )
            }

            handler = handler_map.get(partner)
            if handler:
                return handler()
            else:
                print(f"❌ Unsupported partner: {partner}")
                return False, False

        except Exception as e:
            print(f"❌ Error in DeltaChecker.evaluate: {e}")
            return False, False

    def _process(self, df_invoice, delta_fn, partner, df_list, delta_threshold):
        df_merged, delta_sum, flag = delta_fn(df_invoice)

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

        return delta_sum <= delta_threshold, flag

