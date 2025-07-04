# backend/logistics/tasks.py
import logging
import redis
from celery import shared_task, chain
from django.conf import settings
from logistics.services.delta_checker import DeltaChecker

logger = logging.getLogger(__name__)

# One Redis client for all tasks
redis_client = redis.from_url(settings.REDIS_URL)


@shared_task(name="logistics.tasks.load_invoice_bytes")
def load_invoice_bytes(redis_key: str, redis_key_pdf: str = "") -> dict:
    """
    Subtask 1: fetch the raw file bytes from Redis.
    Returns a context dict containing invoice_bytes and pdf_bytes.
    """
    logger.info("🔄 [load_invoice_bytes] fetching bytes for %s (pdf: %s)", redis_key, redis_key_pdf)

    def _get_bytes(key: str):
        if not key:
            return None
        data = redis_client.get(f"upload:{key}")
        if not data:
            msg = f"No file data in Redis for key upload:{key}"
            logger.error("❌ [load_invoice_bytes] %s", msg)
            raise FileNotFoundError(msg)
        return data

    invoice_bytes = _get_bytes(redis_key)
    pdf_bytes     = _get_bytes(redis_key_pdf)

    logger.info("✅ [load_invoice_bytes] loaded bytes (%d, %s)", len(invoice_bytes), 
                f"{len(pdf_bytes)} bytes" if pdf_bytes else "no pdf")
    return {"invoice_bytes": invoice_bytes, "pdf_bytes": pdf_bytes}


@shared_task(name="logistics.tasks.evaluate_delta")
def evaluate_delta(
    ctx: dict,
    partner: str,
    delta_threshold: float = 20.0
) -> dict:
    """
    Subtask 2: parse invoice, compute delta, build a minimal result payload.
    ctx contains invoice_bytes and pdf_bytes.
    """
    logger.info("🔍 [evaluate_delta] partner=%s, threshold=%.2f", partner, delta_threshold)
    checker = DeltaChecker()

    # We pass the raw bytes through Redis‐backed loader inside DeltaChecker
    success, parsed_ok, df_merged = checker.evaluate(
        partner=partner,
        redis_key="",            
        redis_key_pdf="",  
        df_list=[],
        delta_threshold=delta_threshold,
        invoice_bytes=ctx["invoice_bytes"],
        pdf_bytes=ctx.get("pdf_bytes")
    )

    if df_merged is None:
        msg = f"Failed to compute delta for {partner}"
        logger.error("❌ [evaluate_delta] %s", msg)
        return {"error": msg}

    delta_sum = round(df_merged["Delta"].sum(), 2)
    records = df_merged.to_dict(orient="records")
    logger.info("✅ [evaluate_delta] parsed_ok=%s, delta_sum=%.2f rows=%d",
                parsed_ok, delta_sum, len(records))

    return {
        "delta_ok": success,
        "parsed_ok": parsed_ok,
        "delta_sum": delta_sum,
        "data": records,
    }


@shared_task(name="logistics.tasks.export_sheet")
def export_sheet(ctx: dict, partner: str) -> dict:
    """
    Subtask 3: export the DataFrame to Google Sheets and return the sheet URL.
    ctx comes from evaluate_delta.
    """
    if "error" in ctx:
        # skip export if evaluation failed
        return ctx

    logger.info("📤 [export_sheet] exporting results for partner=%s", partner)
    # The DeltaChecker already exported df_merged inside evaluate, and stored sheet url
    # But if you need to re-export:
    # sheet_url = checker.spreadsheet_exporter.export(df_merged, partner)
    # For simplicity, assume the checker stored it in a module‐level attribute:
    sheet_url = DeltaChecker().spreadsheet_exporter.spreadsheet.url

    logger.info("✅ [export_sheet] sheet_url=%s", sheet_url)
    ctx["sheet_url"] = sheet_url
    return ctx


@shared_task(bind=True, name="logistics.tasks.process_invoice_pipeline")
def process_invoice(
    self,
    partner: str,
    redis_key: str,
    redis_key_pdf: str = "",
    delta_threshold: float = 20.0
) -> dict:
    """
    Entry‐point task: chains load → evaluate → export subtasks, logs pipeline status.
    Returns the final result dict from export_sheet.
    """
    logger.info("▶️ [process_invoice] Starting pipeline %s for partner=%s", self.request.id, partner)

    # Build a chain of the three subtasks
    pipeline = chain(
        load_invoice_bytes.s(redis_key, redis_key_pdf),
        evaluate_delta.s(partner, delta_threshold),
        export_sheet.s(partner)
    )

    # Launch the chain and get its root task id
    result = pipeline.apply_async()
    logger.info("🔗 [process_invoice] Dispatched chain with id %s", result.id)

    # Wait for the chain to finish and return its result
    final = result.get(propagate=False, timeout=300)  # you can adjust timeout
    logger.info("🏁 [process_invoice] Pipeline %s completed with state %s", result.id, result.state)

    return final
