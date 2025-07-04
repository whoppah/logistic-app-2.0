#backend/logistics/services/spreadsheet_exporter.py
import pandas as pd
import gspread
from gspread_formatting import CellFormat, Color, format_cell_range
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
from pathlib import Path


class SpreadsheetExporter:
    def __init__(
        self,
        spreadsheet_name: str = "Invoice spreadsheet",
        share_email: str = "mattia@whoppah.com",
    ):
        # scope for both Sheets & Drive
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # pull in the JSON path you configured in settings
        json_path = Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        if not json_path.exists():
            raise FileNotFoundError(
                f"Google service account file not found at {json_path}"
            )

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            str(json_path), self.scope
        )
        self.client = gspread.authorize(creds)

        self.spreadsheet_name = spreadsheet_name
        self.share_email = share_email
        self.spreadsheet = self._get_or_create_spreadsheet()

    def _get_or_create_spreadsheet(self) -> gspread.Spreadsheet:
        try:
            return self.client.open(self.spreadsheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            sheet = self.client.create(self.spreadsheet_name)
            sheet.share(self.share_email, perm_type="user", role="writer")
            return sheet

    def export(self, df_merged: pd.DataFrame, partner_value: str) -> str:
        """
        Appends df_merged to a worksheet named Sheet_<partner_value>,
        creating it if necessary, and highlights any positive deltas.
        Returns the spreadsheet’s URL.
        """
        title = f"Sheet_{partner_value}"
        try:
            ws = self.spreadsheet.worksheet(title)
            start_row = len(ws.get_all_values()) + 1
            # no headers on append:
            set_with_dataframe(ws, df_merged, row=start_row, col=1, include_column_header=False)
        except gspread.exceptions.WorksheetNotFound:
            # first time: create it and write headers
            ws = self.spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
            set_with_dataframe(ws, df_merged, row=1, col=1, include_column_header=True)
            start_row = 1

        # highlight positive deltas
        if "Delta" in df_merged.columns:
            # 1-based index of the Delta column
            delta_col = df_merged.columns.get_loc("Delta") + 1
            for i, value in enumerate(df_merged["Delta"], start=start_row + 1):
                if value > 0:
                    addr = gspread.utils.rowcol_to_a1(i, delta_col)
                    format_cell_range(ws, addr, CellFormat(backgroundColor=Color(1, 1, 0)))

        return self.spreadsheet.url
