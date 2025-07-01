#backend/logistics/views.py
from logistics.services.delta_evaluator import evaluate_delta_from_files

def run_delta_view(request):
    partner = request.GET.get("partner")
    redis_key = request.GET.get("redis_key")
    redis_key_pdf = request.GET.get("redis_key_pdf") 
    df_list = []

    success, parsed, df = evaluate_delta_from_files(
        partner_value=partner,
        redis_key=redis_key,
        redis_key_pdf=redis_key_pdf,
        delta_threshold=20,
        df_list=df_list
    )

    if not parsed:
        return JsonResponse({"error": "Parsing failed"}, status=400)

    return JsonResponse({
        "partner": partner,
        "delta_ok": success,
        "rows_returned": len(df) if df is not None else 0
    })
