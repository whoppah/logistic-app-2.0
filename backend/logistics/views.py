#backend/logistics/views.py
import json
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from logistics.services.database_service import DatabaseService
from logistics.services.spreadsheet_exporter import SpreadsheetExporter
from logistics.parsers.brenger import brenger_read_pdf
from logistics.delta.brenger import compute_delta_brenger
from redis import Redis


class CheckDeltaView(APIView):
    """
    Endpoint to check delta for a given logistics partner and export results.
    """

    def post(self, request):
        try:
            partner = request.data.get("partner")
            redis_key = request.data.get("redis_key")
            redis_key_pdf = request.data.get("redis_key_pdf")  # for libero
            delta_threshold = float(request.data.get("delta_threshold", 20))

            if not partner or not redis_key:
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            partner = partner.strip().lower()

            # Initialize services
            db_service = DatabaseService()
            exporter = SpreadsheetExporter()
            redis_client = Redis.from_url(os.getenv("REDIS_URL"))

            # Get CMS orders
            df_order = db_service.get_orders_dataframe(partner)

            # Dispatcher: Load + Parse + Compute
            if partner == "brenger":
                df = brenger_read_pdf(redis_key)
                df_merged, delta_sum, flag = compute_delta_brenger(df, df_order)

            elif partner == "wuunder":
                from logistics.parsers.wuunder import wuunder_read_pdf
                from logistics.delta.wuunder import compute_delta_wuunder
                df = wuunder_read_pdf(redis_key)
                df_merged, delta_sum, flag = compute_delta_wuunder(df, df_order)

            elif partner == "swdevries":
                from logistics.parsers.swdevries import swdevries_read_xlsx
                from logistics.delta.generic import compute_delta_other_partners
                df = swdevries_read_xlsx(redis_key)
                df_merged, delta_sum, flag = compute_delta_other_partners(df, df_order, partner)

            elif partner == "libero_logistics":
                from logistics.parsers.libero import libero_logistics_read_xlsx
                from logistics.delta.generic import compute_delta_other_partners
                df = libero_logistics_read_xlsx(redis_key, redis_key_pdf)
                df_merged, delta_sum, flag = compute_delta_other_partners(df, df_order, partner)

            else:
                return Response({"error": f"Unsupported partner: {partner}"}, status=status.HTTP_400_BAD_REQUEST)

            # Export to spreadsheet
            sheet_url = exporter.export(df_merged, partner)

            # Return results
            result = {
                "delta_sum": round(delta_sum, 2),
                "delta_ok": delta_sum <= delta_threshold,
                "sheet_url": sheet_url,
                "message": "Success" if flag else "Data matched but empty."
            }
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
