# backend/logistics/views.py
import uuid
from django.core.cache import cache
from django.core.files.base import ContentFile
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .tasks import process_invoice

class CheckDeltaView(APIView):
    """
    Endpoint to start the delta‐check Celery task.
    """

    def post(self, request):
        partner        = request.data.get("partner")
        redis_key      = request.data.get("redis_key")
        redis_key_pdf  = request.data.get("redis_key_pdf", None)
        delta_threshold = float(request.data.get("delta_threshold", 20.0))

        if not partner or not redis_key:
            return Response({"error": "Missing required fields."},
                            status=status.HTTP_400_BAD_REQUEST)

        # launch Celery task
        task = process_invoice.delay(partner, redis_key, redis_key_pdf, delta_threshold)

        return Response(
            {"task_id": task.id},
            status=status.HTTP_202_ACCEPTED
        )
4. Polling & result endpoints

Add two small methods:

# backend/logistics/views.py

from celery.result import AsyncResult

class TaskStatusView(APIView):
    """
    Poll this to get current status of a Celery task.
    """
    def get(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response({"error": "Missing task_id"}, status=status.HTTP_400_BAD_REQUEST)

        res = AsyncResult(task_id)
        return Response({
            "state": res.state,
        })


class TaskResultView(APIView):
    """
    Once TaskStatus returns SUCCESS, GET here to fetch the payload.
    """
    def get(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response({"error": "Missing task_id"}, status=status.HTTP_400_BAD_REQUEST)

        res = AsyncResult(task_id)
        if res.state != "SUCCESS":
            return Response({"error": "Not ready", "state": res.state}, status=status.HTTP_202_ACCEPTED)

        result = res.result or {}
        return Response(result, status=status.HTTP_200_OK)

class UploadInvoiceFile(APIView):
    """
    Upload invoice files and store them temporarily in Django’s cache.
    Returns redis-style keys to use in /check-delta/.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        files = request.FILES.getlist("file")
        if not files:
            return Response({"error": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        redis_key = None
        redis_key_pdf = None

        for f in files:
            ext = f.name.rsplit(".", 1)[-1].lower()
            key = str(uuid.uuid4())
            # read bytes and cache for 10 min
            file_bytes = f.read()
            cache.set(key, file_bytes, timeout=600)

            if ext in ("xlsx", "xls"):
                redis_key = key
            elif ext == "pdf":
                redis_key_pdf = key

        return Response(
            {
                "redis_key": redis_key,
                "redis_key_pdf": redis_key_pdf,
            },
            status=status.HTTP_200_OK,
        )
