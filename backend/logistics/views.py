#backend/logistics/views.py
import os
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from logistics.services.delta_evaluator import DeltaEvaluator


class CheckDeltaView(APIView):
    """
    Endpoint to check delta for a given logistics partner and export results.
    """

    def post(self, request):
        try:
            partner = request.data.get("partner")
            redis_key = request.data.get("redis_key")
            redis_key_pdf = request.data.get("redis_key_pdf")  # for Libero
            delta_threshold = float(request.data.get("delta_threshold", 20))

            if not partner or not redis_key:
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            # Use evaluator
            evaluator = DeltaEvaluator()
            df_list = []
            delta_ok, flag, df_merged = evaluator.evaluate(
                partner_value=partner,
                redis_key=redis_key,
                redis_key_pdf=redis_key_pdf,
                delta_threshold=delta_threshold,
                df_list=df_list
            )

            if df_merged is None:
                return Response({"error": "Delta evaluation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            result = {
                "delta_sum": round(df_merged["Delta"].sum(), 2),
                "delta_ok": delta_ok,
                "sheet_url": evaluator.exporter.spreadsheet.url,
                "message": "Success" if flag else "Data matched but empty."
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
