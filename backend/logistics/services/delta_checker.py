# backend/logistics/services/delta_checker.py
import pandas as pd
from backend.logistics.db.query import get_df_from_query_db
from backend.logistics.extraction.parsers import (
    brenger_read_pdf, wuunder_read_pdf, 
    swdevries_read_xlsx, libero_logistics_read_xlsx, 
    transpoksi_read_pdf, magic_movers_read_xlsx
)
from backend.logistics.processing.delta import (
    compute_delta_brenger, compute_delta_wuunder, 
    compute_delta_other_partners, compute_delta_magic_movers
)
from backend.logistics.export.google_sheets import export_to_spreadsheet


class DeltaCheckerService:
    def __init__(self, partner_value, redis_key, df_list, redis_key_pdf="", file_name="", file_name_pdf="", delta_condition=20):
        self.partner_value = partner_value.lower().strip()
        self.redis_key = redis_key
        self.redis_key_pdf = redis_key_pdf
        self.file_name = file_name
        self.file_name_pdf = file_name_pdf
        self.delta_condition = delta_condition
        self.df_list = df_list

    def run(self):
        try:
            df_order = get_df_from_query_db(partner_value=self.partner_value)

            partner_map = {
                "brenger": self._handle_brenger,
                "wuunder": self._handle_wuunder,
                "libero_logistics": self._handle_libero,
                "swdevries": self._handle_swdevries,
                "transpoksi": self._handle_transpoksi,
                "magic_movers": self._handle_magic_movers
            }

            handler = partner_map.get(self.partner_value)
            if handler:
                return handler(df_order)
            else:
                print(f"Unsupported partner: {self.partner_value}")
                return False, False
        except Exception as e:
            print(f"Error reading file for {self.partner_value}: {e}")
            return False, False

    def _append_or_summarize(self, df_merged, delta_sum, flag):
        if not df_merged.empty:
            df_merged["Type"] = "data"
            df_merged["partner"] = self.partner_value
            self.df_list.append(df_merged)
        elif delta_sum == 0 and flag:
            summary_row = pd.DataFrame([{
                "Partner": self.partner_value,
                "Delta sum": delta_sum,
                "Message": "All prices match perfectly",
                "Type": "summary"
            }])
            self.df_list.append(summary_row)
        return delta_sum <= self.delta_condition, flag

    def _handle_brenger(self, df_order):
        df = brenger_read_pdf(redis_key=self.redis_key)
        df_merged, delta_sum, flag = compute_delta_brenger(df, df_order)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)

    def _handle_wuunder(self, df_order):
        df = wuunder_read_pdf(self.redis_key)
        df_merged, delta_sum, flag = compute_delta_wuunder(df, df_order)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)

    def _handle_libero(self, df_order):
        df = libero_logistics_read_xlsx(self.redis_key, self.redis_key_pdf)
        df_merged, delta_sum, flag = compute_delta_other_partners(df, df_order, self.partner_value)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)

    def _handle_swdevries(self, df_order):
        df = swdevries_read_xlsx(self.redis_key)
        df_merged, delta_sum, flag = compute_delta_other_partners(df, df_order, self.partner_value)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)

    def _handle_transpoksi(self, df_order):
        df = transpoksi_read_pdf(self.redis_key)
        df_merged, delta_sum, flag = compute_delta_other_partners(df, df_order, self.partner_value)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)

    def _handle_magic_movers(self, df_order):
        df = magic_movers_read_xlsx(invoice_value=None, date_value=None, redis_key=self.redis_key)  # Update if needed
        df_merged, delta_sum, flag = compute_delta_magic_movers(df, df_order, self.partner_value)
        export_to_spreadsheet(df_merged, self.partner_value)
        return self._append_or_summarize(df_merged, delta_sum, flag)
