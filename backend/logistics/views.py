# backend/logistics/views.py
import uuid
from django.core.cache import cache
from django.core.files.base import ContentFile
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

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
