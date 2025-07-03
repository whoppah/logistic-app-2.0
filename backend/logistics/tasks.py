# backend/logistics/tasks.py

from celery import shared_task
from django.core.cache import cache
from .services.delta_checker import DeltaChecker

@shared_task(bind=True)
def process_invoice(self, partner: str, redis_key: str, redis_key_pdf: str = None, delta_threshold: float = 20.0):
    """
    Celery task to parse invoice, compute delta, export to Google Sheets.
    Returns a dict with the result data.
    """
    # Load cached file bytes
    invoice_bytes = cache.get(redis_key)
    pdf_bytes     = cache.get(redis_key_pdf) if redis_key_pdf else None

    checker = DeltaChecker()
    # df_list is only used internally to collect for spreadsheet export; we ignore it here
    success, flag, df_merged = checker.evaluate(
        partner=partner,
        redis_key=redis_key,
        redis_key_pdf=redis_key_pdf or "",
        delta_threshold=delta_threshold,
        df_list=[]
    )

    if df_merged is None:
        # signal failure
        return {
            "error": f"Could not compute delta for {partner}",
        }

    # prepare JSON‐serializable payload
    data = df_merged.to_dict(orient="records")
    delta_sum = round(df_merged["Delta"].sum(), 2)
    sheet_url = checker.spreadsheet_exporter.spreadsheet.url

    return {
        "delta_ok": success,
        "parsed_ok": flag,
        "delta_sum": delta_sum,
        "data": data,
        "sheet_url": sheet_url,
    }
