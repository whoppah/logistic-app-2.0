# backend/logistics/views.py
import uuid
import redis

from django.conf import settings
from celery import chain
from celery.result import AsyncResult
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .tasks import load_invoice_bytes, evaluate_delta, export_sheet

redis_client = redis.from_url(settings.REDIS_URL)


class UploadInvoiceFile(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        files = request.FILES.getlist("file")
        if not files:
            return Response({"error": "No files provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        redis_key = None
        redis_key_pdf = None

        for f in files:
            ext = f.name.rsplit(".", 1)[-1].lower()
            key = str(uuid.uuid4())
            raw = f.read()
            redis_client.setex(f"upload:{key}", 600, raw)
            if ext in ("xlsx", "xls"):
                redis_key = key
            elif ext == "pdf":
                redis_key_pdf = key

        return Response(
            {"redis_key": redis_key, "redis_key_pdf": redis_key_pdf},
            status=status.HTTP_200_OK,
        )


class CheckDeltaView(APIView):
    """
    Instead of firing only the wrapper task, build and dispatch the chain
    and return *that* chain’s ID so the front-end polls the real long-running job.
    """

    def post(self, request):
        partner         = request.data.get("partner")
        redis_key       = request.data.get("redis_key")
        redis_key_pdf   = request.data.get("redis_key_pdf", "")
        delta_threshold = float(request.data.get("delta_threshold", 20.0))

        if not partner or not redis_key:
            return Response({"error": "Missing required fields."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Build & launch the exact same chain as your wrapper did:
        job = chain(
            load_invoice_bytes.s(redis_key, redis_key_pdf),
            evaluate_delta.s(partner, delta_threshold),
            export_sheet.s(partner)
        )()

        # Return the *chain* ID (i.e. the ID of the last sub-task)
        return Response({"task_id": job.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """
    Poll the real chain ID until it reaches SUCCESS or FAILURE.
    """

    def get(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response({"error": "Missing task_id"},
                            status=status.HTTP_400_BAD_REQUEST)

        res = AsyncResult(task_id)
        return Response({"state": res.state}, status=status.HTTP_200_OK)


class TaskResultView(APIView):
    """
    Once TaskStatusView returns state==="SUCCESS", fetch the final payload.
    """

    def get(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response({"error": "Missing task_id"},
                            status=status.HTTP_400_BAD_REQUEST)

        res = AsyncResult(task_id)
        if res.state != "SUCCESS":
            return Response({"error": "Not ready", "state": res.state},
                            status=status.HTTP_202_ACCEPTED)

        return Response(res.result or {}, status=status.HTTP_200_OK)
