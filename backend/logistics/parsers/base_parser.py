#backend/logistics/parsers/base_parser.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd


class BaseParser(ABC):
    """
    Abstract base class for all invoice parsers.

    Each subclass must implement `parse()`, which returns a DataFrame
    containing structured invoice/shipment data for delta comparison
    or analytics.

    You can optionally override:
    - extract_metadata(): to extract summary info like invoice number/date
    - validate(): to ensure data integrity
    """

    def __init__(self):
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def parse(self, file_bytes: bytes, context: Optional[dict] = None) -> pd.DataFrame:
        """
        Main method to parse file bytes into a structured DataFrame.

        Args:
            file_bytes (bytes): Raw content of the file (PDF, XLSX, CSV)
            context (dict, optional): Additional inputs such as a second file or config flags

        Returns:
            pd.DataFrame: The parsed invoice or shipment data
        """
        pass

    def extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Optional hook to extract invoice metadata from the parsed DataFrame.

        Args:
            df (pd.DataFrame): Parsed result

        Returns:
            dict: Dictionary with metadata like invoice number, totals, etc.
        """
        return {}

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Optional validation step to ensure the DataFrame is well-formed.

        This can be overridden in specific parsers to enforce field constraints.

        Args:
            df (pd.DataFrame): The parsed invoice data

        Returns:
            bool: True if the data passes validation
        """
        if df.empty:
            raise ValueError("Parsed DataFrame is empty.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Parsed object must be a pandas DataFrame.")

        return True
