#backend/logistics/delta/base.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple


class BaseDeltaCalculator(ABC):
    """
    Abstract base class for computing delta between invoice data and internal CMS data.
    """

    def __init__(self, df_invoice: pd.DataFrame, df_order: pd.DataFrame):
        """
        Args:
            df_invoice (pd.DataFrame): DataFrame parsed from invoice (PDF/XLSX).
            df_order (pd.DataFrame): DataFrame retrieved from internal system (CMS).
        """
        self.df_invoice = df_invoice
        self.df_order = df_order

    @abstractmethod
    def compute(self) -> Tuple[pd.DataFrame, float, bool]:
        """
        Compute the delta between invoice and expected prices.

        Returns:
            Tuple[pd.DataFrame, float, bool]:
                - merged DataFrame with delta information
                - sum of delta values
                - flag indicating whether comparison was possible
        """
        pass

    def filter_positive_delta(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter rows where delta is positive (invoice > expected price).

        Args:
            df (pd.DataFrame): Computed DataFrame with Delta column.

        Returns:
            pd.DataFrame: Subset with positive Delta values.
        """
        return df[df["Delta"] > 0].copy()

    def validate_columns(self, df: pd.DataFrame, required: list[str]) -> None:
        """
        Ensure required columns exist in the DataFrame.

        Raises:
            ValueError: if any required column is missing.
        """
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
