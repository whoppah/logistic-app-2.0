# backend/logistics/views.py
import traceback
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from logistics.services.delta_checker import DeltaChecker


class CheckDeltaView(APIView):
    """
    Endpoint to check delta for a given logistics partner and export results.
    """

    def post(self, request):
        try:
            partner = request.data.get("partner")
            redis_key = request.data.get("redis_key")
            redis_key_pdf = request.data.get("redis_key_pdf")  # optional
            delta_threshold = float(request.data.get("delta_threshold", 20))

            if not partner or not redis_key:
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            df_list = []
            checker = DeltaChecker()
            delta_ok, flag, df_merged = checker.evaluate(
                partner=partner,
                redis_key=redis_key,
                redis_key_pdf=redis_key_pdf,
                delta_threshold=delta_threshold,
                df_list=df_list
            )

            if df_merged is None:
                return Response({"error": "Delta evaluation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Prepare data for frontend
            table_data = df_merged.to_dict(orient="records")
            delta_sum = round(df_merged["Delta"].sum(), 2)

            result = {
                "delta_sum": delta_sum,
                "delta_ok": delta_ok,
                "data": table_data,
                "sheet_url": checker.spreadsheet_exporter.spreadsheet.url,
                "message": "Success" if flag else "Data matched but empty."
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UploadInvoiceFile(APIView):
    """
    Upload invoice files and store them temporarily (PDF and/or XLSX).
    Returns redis-style keys to use in /check-delta/.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        try:
            files = request.FILES.getlist("file")
            if not files:
                return Response({"error": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

            redis_key = None
            redis_key_pdf = None

            for f in files:
                extension = f.name.split(".")[-1].lower()
                key = str(uuid.uuid4())
                filename = f"{key}.{extension}"
                save_path = os.path.join(settings.BASE_DIR, "backend", "logistics", "slack", filename)

                # Save the file
                path = default_storage.save(save_path, ContentFile(f.read()))

                if extension in ["xlsx", "xls"]:
                    redis_key = key
                elif extension == "pdf":
                    redis_key_pdf = key

            return Response(
                {
                    "redis_key": redis_key,
                    "redis_key_pdf": redis_key_pdf,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
