# backend/logistics/tasks.py
import logging
import redis
from celery import shared_task, chain
from django.conf import settings
from logistics.services.delta_checker import DeltaChecker

logger = logging.getLogger(__name__)
redis_client = redis.from_url(settings.REDIS_URL)


@shared_task(name="logistics.tasks.load_invoice_bytes")
def load_invoice_bytes(redis_key: str, redis_key_pdf: str = "") -> dict:
    logger.info("🔄 [load_invoice_bytes] fetching %s / %s", redis_key, redis_key_pdf)
    def _get_bytes(key):
        if not key:
            return None
        data = redis_client.get(f"upload:{key}")
        if not data:
            msg = f"No data in Redis for upload:{key}"
            logger.error("❌ %s", msg)
            raise FileNotFoundError(msg)
        return data

    return {
        "invoice_bytes": _get_bytes(redis_key),
        "pdf_bytes":     _get_bytes(redis_key_pdf),
    }


@shared_task(name="logistics.tasks.evaluate_delta")
def evaluate_delta(ctx: dict, partner: str, delta_threshold: float) -> dict:
    logger.info("🔍 [evaluate_delta] partner=%s", partner)
    checker = DeltaChecker()
    # Now DeltaChecker should accept invoice_bytes & pdf_bytes from ctx directly
    success, parsed_ok, df_merged = checker.evaluate(
        partner=partner,
        redis_key="",         # not used
        redis_key_pdf="",     # not used
        df_list=[],
        delta_threshold=delta_threshold,
        invoice_bytes=ctx["invoice_bytes"],
        pdf_bytes=ctx["pdf_bytes"],
    )

    if df_merged is None:
        return {"error": f"Delta failed for {partner}"}

    return {
        "delta_ok":   success,
        "parsed_ok":  parsed_ok,
        "delta_sum":  round(df_merged["Delta"].sum(), 2),
        "data":       df_merged.to_dict(orient="records"),
    }


@shared_task(name="logistics.tasks.export_sheet")
def export_sheet(ctx: dict, partner: str) -> dict:
    if "error" in ctx:
        return ctx
    logger.info("📤 [export_sheet] partner=%s", partner)
    # assume DeltaChecker already did the export internally
    sheet_url = DeltaChecker().spreadsheet_exporter.spreadsheet.url
    ctx["sheet_url"] = sheet_url
    return ctx


@shared_task(bind=True, name="logistics.tasks.process_invoice_pipeline")
def process_invoice_pipeline(
    self,
    partner: str,
    redis_key: str,
    redis_key_pdf: str = "",
    delta_threshold: float = 20.0
) -> dict:
    """
    Dispatches a chain of subtasks, then returns immediately with the chain id.
    Your view should return {"task_id": chain.id} and let the frontend poll.
    """
    logger.info("▶️ Starting pipeline %s for %s", self.request.id, partner)

    # build and apply the chain
    job = chain(
        load_invoice_bytes.s(redis_key, redis_key_pdf),
        evaluate_delta.s(partner, delta_threshold),
        export_sheet.s(partner)
    )()
    logger.info("🔗 Dispatched chain, id=%s", job.id)

    return {"task_id": job.id}
