#backend/logistics/services/spreadsheet_exporter.py
import os
import pandas as pd
import gspread
from gspread_formatting import CellFormat, Color, format_cell_range
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials


class SpreadsheetExporter:
    def __init__(self, spreadsheet_name="Invoice spreadsheet", share_email="biancotto.mattia.mb@gmail.com"):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        json_path = os.path.join(os.getcwd(), "Facturen_Logistiek", "upbeat-flame-451212-j5-8d545d206f5e.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, self.scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet_name = spreadsheet_name
        self.spreadsheet = self._get_or_create_spreadsheet()
        self.share_email = share_email

    def _get_or_create_spreadsheet(self):
        try:
            return self.client.open(self.spreadsheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            sheet = self.client.create(self.spreadsheet_name)
            sheet.share(self.share_email, perm_type='user', role='writer')
            return sheet

    def export(self, df_merged: pd.DataFrame, partner_value: str) -> str:
        title = f"Sheet_{partner_value}"
        try:
            worksheet = self.spreadsheet.worksheet(title)
            last_row = len(worksheet.get_all_values())
            set_with_dataframe(worksheet, df_merged, row=last_row + 1, col=1, include_column_header=False)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows="100", cols="20")
            set_with_dataframe(worksheet, df_merged, row=1, col=1, include_column_header=True)
            last_row = 1

        if 'Delta' in df_merged.columns:
            delta_index = df_merged.columns.get_loc('Delta') + 1
            for i, delta in enumerate(df_merged['Delta'], start=last_row + 1):
                if delta > 0:
                    cell = worksheet.cell(i, delta_index)
                    format_cell_range(worksheet, cell.address, CellFormat(backgroundColor=Color(1, 1, 0)))

        return self.spreadsheet.url
