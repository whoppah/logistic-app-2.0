# backend/logistics/views.py
import uuid
import redis
import os
import pandas as pd
import json
import logging
import requests
from collections import defaultdict
from django.conf import settings
from celery import chain
from celery.result import AsyncResult
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Avg, Sum, Count, F, FloatField, ExpressionWrapper, Value, Func
from django.db.models.functions import Cast, TruncMonth
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError

from logistics.models import InvoiceRun, InvoiceLine

from .tasks import load_invoice_bytes, evaluate_delta#, export_sheet
from .services.slack_service import SlackService
from slack_sdk.errors import SlackApiError

redis_client = redis.from_url(settings.REDIS_URL)
logger = logging.getLogger(__name__)

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
            evaluate_delta.s(partner, delta_threshold)
            #export_sheet.s(partner)
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

        try:
            result = res.result or {}
        except Exception as e:
            # wrap any deserialization or application‐level error
            return Response(
                {"error": "Failed to fetch task result", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(result, status=status.HTTP_200_OK)

class AnalyticsView(APIView):
    """
    Returns comprehensive analytics.
    """
    def get(self, request):
        try:
            # Base querysets
            runs  = InvoiceRun.objects.all()
            lines = InvoiceLine.objects.all()

            # 1) Totals & averages
            total_runs        = runs.count()
            avg_delta_per_run = runs.aggregate(avg=Avg("delta_sum"))["avg"] or 0.0

            # 2) Top partner
            top = (
                runs.values("partner")
                    .annotate(cnt=Count("id"))
                    .order_by("-cnt")
                    .first()
            )
            top_partner = top["partner"] if top else ""

            # 3) Positive‐delta lines
            pos = lines.filter(delta__gt=0).annotate(
                over=ExpressionWrapper(F("delta"), output_field=FloatField())
            )
            avg_over_per_order = pos.aggregate(avg=Avg("over"))["avg"] or 0.0

            # 4) Over‐charge by partner
            over_per_partner = {
                rec["run__partner"]: float(rec["total_over"])
                for rec in pos.values("run__partner")
                             .annotate(total_over=Sum("over"))
                             .order_by("-total_over")
            }

            # 5) Over‐charge by country
            country_acc = defaultdict(float)
            for route, over in pos.values_list("route", "over"):
                buyer = route.split("-",1)[0] if route and "-" in route else route or "Unknown"
                country_acc[buyer] += over
            over_per_country = dict(sorted(country_acc.items(), key=lambda x: x[1], reverse=True))

            # 6) Monthly trend
            trend_dict, partners = defaultdict(dict), set()
            for rec in pos.annotate(month=TruncMonth("invoice_date")) \
                          .values("month", "run__partner") \
                          .annotate(total_over=Sum("over")):
                m = rec["month"].strftime("%Y-%m")
                p = rec["run__partner"]
                trend_dict[m][p] = float(rec["total_over"])
                partners.add(p)

            trend_data    = [{"month": m, **trend_dict[m]} for m in sorted(trend_dict)]
            partners_list = sorted(partners)

            # 7) Top 5 lossy routes by **average** over-charge per order
            route_qs = (
                pos.values("route")
                   .annotate(
                       total_over=Sum("over"),
                       order_count=Count("id")
                   )
                   .filter(order_count__gt=0)
                   .annotate(
                       avg_over=ExpressionWrapper(
                           F("total_over") / F("order_count"),
                           output_field=FloatField()
                       )
                   )
                   .order_by("-avg_over")[:5]
            )
            top_routes = [
                {
                    "route":     rec["route"],
                    "avg_over":  round(rec["avg_over"], 2),
                    "total_over": float(rec["total_over"]),
                    "orders":    rec["order_count"],
                }
                for rec in route_qs
            ]

            # 8) Over-charge by category & weight (average per item)
            cat_wt_qs = (
                pos.values("category_lvl_1_and_2", "weight")
                   .annotate(
                       total_over=Sum("over"),
                       count=Count("id"),
                   )
                   .annotate(
                       avg_over=ExpressionWrapper(
                           F("total_over") / F("count"),
                           output_field=FloatField()
                       )
                   )
            )
            
            # Build a list of { category, weight, avg_over, total_over, count }
            category_weight = [
                {
                    "category":    rec["category_lvl_1_and_2"],
                    "weight":      float(rec["weight"]),
                    "total_over":  float(rec["total_over"]),
                    "count":       rec["count"],
                    "avg_over":    round(rec["avg_over"], 2),
                }
                for rec in cat_wt_qs
            ]

            return Response({
                "total_runs":         total_runs,
                "avg_delta_per_run":  round(avg_delta_per_run, 2),
                "top_partner":        top_partner,
                "avg_over_per_order": round(avg_over_per_order, 2),
                "over_per_partner":   over_per_partner,
                "over_per_country":   over_per_country,
                "trend_data":         trend_data,
                "partners_list":      partners_list,
                "top_routes":         top_routes,
                "category_weight":    category_weight,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Print stack to logs and return error to frontend
            import traceback; traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SlackMessagesView(APIView):
    """
    GET /logistics/slack/messages/
    Returns only top‐level messages (thread_ts == ts or no thread_ts),
    with reply_count, reactions & files.
    """
    def get(self, request):
        try:
            slack = SlackService()
            all_msgs = slack.get_latest_messages(limit=50)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Build reply index
        replies_by_parent = {}
        for m in all_msgs:
            parent = m.get("thread_ts") or m.get("ts")
            if parent != m.get("ts"):
                replies_by_parent.setdefault(parent, []).append(m)

        out = []
        for m in all_msgs:
            ts = m.get("ts")
            # skip pure replies—only show parents
            if m.get("thread_ts") and m["thread_ts"] != ts:
                continue

            # assemble files
            files = [
                {
                    "id":       f.get("id"),
                    "name":     f.get("name"),
                    "mimetype": f.get("mimetype"),
                    "url":      f.get("url_private"),
                }
                for f in m.get("files", [])
            ]

            # assemble reactions
            reactions = [
                {
                    "name":  r.get("name"),
                    "count": r.get("count"),
                    "me":    ts in r.get("users", []),
                }
                for r in m.get("reactions", [])
            ]

            out.append({
                "ts":           ts,
                "user":         m.get("user"),
                "user_name":    m.get("user_profile", {}).get("real_name", m.get("user")),
                "text":         m.get("text", ""),
                "reply_count":  m.get("reply_count", 0),
                "reactions":    reactions,
                "files":        files,
            })

        # sort newest-first
        out.sort(key=lambda x: float(x["ts"]), reverse=True)
        return Response(out, status=status.HTTP_200_OK)


class SlackThreadView(APIView):
    """
    GET /logistics/slack/threads/?thread_ts=12345
    Returns parent + all replies in chronological order,
    each with reactions & files.
    """
    def get(self, request):
        thread_ts = request.query_params.get("thread_ts")
        if not thread_ts:
            return Response(
                {"error": "Missing thread_ts parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            slack = SlackService()
            thread_msgs = slack.get_thread(thread_ts, limit=100)
        except SlackApiError as e:
            return Response(
                {"error": "Failed to fetch thread from Slack."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        out = []
        for m in thread_msgs:
            ts = m.get("ts")
            if not ts:
                continue

            files = [
                {
                    "id":       f.get("id"),
                    "name":     f.get("name"),
                    "mimetype": f.get("mimetype"),
                    "url":      f.get("url_private"),
                }
                for f in m.get("files", [])
            ]

            reactions = [
                {
                    "name":  r.get("name"),
                    "count": r.get("count"),
                    "me":    ts in r.get("users", []),
                }
                for r in m.get("reactions", [])
            ]

            out.append({
                "ts":           ts,
                "ts_float":     float(ts),
                "user":         m.get("user"),
                "user_name":    m.get("user_profile", {}).get("real_name", m.get("user")),
                "text":         m.get("text", ""),
                "reactions":    reactions,
                "files":        files,
            })

        # chronological: parent first, then replies
        out.sort(key=lambda x: x["ts_float"])
        return Response(out, status=status.HTTP_200_OK)

class SlackReactView(APIView):
    """
    POST /logistics/slack/react/
    Body: { ts: "...", reaction: "white_check_mark" }
    Adds/removes the given reaction on the given message.
    """
    def post(self, request):
        ts       = request.data.get("ts")
        reaction = request.data.get("reaction")
        if not ts or not reaction:
            return Response(
                {"error": "Missing ts or reaction"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            slack = SlackService()
            slack.react_to_message(ts, reaction)
            return Response({"ok": True}, status=status.HTTP_200_OK)
        except SlackApiError as e:
            print(f"❌ SlackReactView SlackApiError: {e.response['error']}")
            return Response(
                {"error": e.response["error"]},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            print(f"❌ SlackReactView error: {e}")
            return Response(
                {"error": "Internal error adding reaction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SlackFileDownloadView(APIView):
    """
    Proxy-download a Slack-hosted file for the front end,
    so we can attach our bot token server-side and avoid CORS issues.
    GET /logistics/slack/download/?file_url=…
    """
    def get(self, request):
        file_url = request.query_params.get("file_url")
        if not file_url:
            return HttpResponseBadRequest("Missing file_url param")

        headers = {
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"
        }

        try:
            # stream=True so we don't load entire file into memory at once
            resp = requests.get(file_url, headers=headers, stream=True, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            # something went wrong fetching from Slack
            return HttpResponseServerError(f"Slack download failed: {e}")

        # pass through the content and content-type
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        content = resp.raw.read()  # read from the streamed response

        return HttpResponse(content, content_type=content_type)

class PricingMetadataView(APIView):
    """
    GET /logistics/pricing/metadata/?partner=brenger
    Returns the list of routes (the JSON keys minus the two fixed ones)
    and the list of categories.
    """
    def get(self, request):
        partner = request.query_params.get("partner")
        if not partner:
            return Response({"error": "Missing partner"}, status=status.HTTP_400_BAD_REQUEST)

        path = os.path.join(settings.PRICING_DATA_PATH, f"prijslijst_{partner}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return Response({"error": f"No pricing for {partner}"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Could not load metadata"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # fixed fields:
        cats = list(data.get("CMS category", {}).values())
        # everything else that isn't "CMS category" or "Weightclass"
        routes = [k for k in data.keys() if k not in ("CMS category", "Weightclass","Pakket + Koeriers")]

        return Response({
            "categories": sorted(cats),
            "routes":     sorted(routes),
        }, status=status.HTTP_200_OK)

class PricingLookupView(APIView):
    """
    GET /logistics/pricing/
    Query params: partner, route, category
    Returns: { prices: { "<weight>": <price>, ... } }
    """
    def get(self, request):
        partner  = request.query_params.get("partner")
        route    = request.query_params.get("route")
        category = request.query_params.get("category")
        if not (partner and route and category):
            return Response(
                {"error": "Missing partner, route or category"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # load your JSON file
        pricing_path = os.path.join(settings.PRICING_DATA_PATH,
                                    f"prijslijst_{partner}.json")
        try:
            df = pd.read_json(pricing_path)
        except Exception:
            return Response(
                {"error": f"Cannot load pricing for {partner}."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # filter rows matching category & route
        df = df[
            (df["CMS category"] == category)
        ][["Weightclass", route]]

        if df.empty:
            return Response(
                {"error": "No matching price found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # build weight→price map
        weight_map = {
            str(int(w)): float(p)
            for w, p in zip(df["Weightclass"], df[route])
        }

        return Response({"prices": weight_map}, status=status.HTTP_200_OK)
