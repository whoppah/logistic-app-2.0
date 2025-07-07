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
from django.db.models import Avg, Count

from .models import InvoiceRun
from .tasks import load_invoice_bytes, evaluate_delta, export_sheet
from .services.slack_service import SlackService

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

class AnalyticsView(APIView):
    """
    Returns totals and averages from InvoiceRun.
    """

    def get(self, request):
        qs = InvoiceRun.objects.all()
        total_files = qs.count()
        avg_delta   = qs.aggregate(avg=Avg("delta_sum"))["avg"] or 0.0
        top = (
            qs.values("partner")
              .annotate(cnt=Count("id"))
              .order_by("-cnt")
              .first()
        )
        top_partner = top["partner"] if top else ""

        return Response({
            "total_files": total_files,
            "avg_delta":   round(avg_delta, 2),
            "top_partner": top_partner,
        }, status=status.HTTP_200_OK)

class SlackMessagesView(APIView):
    def get(self, request):
        try:
            slack = SlackService()
            msgs  = slack.get_latest_messages(limit=50)
        except Exception as e:
            # catch both RuntimeError (missing env) or SlackApiError
            print(f"❌ SlackMessagesView error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        out = []
        for m in msgs:
            try:
                ts = m.get("ts")
                if not ts:
                    continue
                parent_ts = m.get("thread_ts") if m.get("thread_ts") != ts else ts
                replies = [
                    msg for msg in msgs
                    if msg.get("thread_ts") == parent_ts and msg.get("ts") != parent_ts
                ]
                out.append({
                    "ts":          ts,
                    "user_name":   m.get("user_profile", {}).get("real_name", m.get("user")),
                    "text":        m.get("text", ""),
                    "reply_count": len(replies),
                })
            except Exception as inner:
                print(f"⚠️ Skipping malformed message entry: {inner}")
                continue

        return Response(out, status=status.HTTP_200_OK)


class SlackThreadView(APIView):
    """
    GET /logistics/slack/threads/?thread_ts=12345 → return the thread messages
    """
    def get(self, request):
        thread_ts = request.query_params.get("thread_ts")
        if not thread_ts:
            return Response(
                {"error": "Missing thread_ts parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize SlackService, validating env vars
        try:
            slack = SlackService()
        except Exception as e:
            # Could be missing token or channel in settings
            print(f"❌ SlackThreadView init error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Fetch the thread from Slack
        try:
            messages = slack.get_thread(thread_ts, limit=100)
        except SlackApiError as e:
            print(f"❌ Slack API error in get_thread: {e.response['error']}")
            return Response(
                {"error": "Failed to fetch thread from Slack."},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            print(f"❌ Unexpected error in get_thread: {e}")
            return Response(
                {"error": "Internal error fetching Slack thread."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Build the response, skipping any malformed entries
        out = []
        for m in messages:
            ts_val = m.get("ts")
            text   = m.get("text", "")
            user   = m.get("user")
            user_name = m.get("user_profile", {}).get("real_name") or user

            if not ts_val:
                # skip entries without a timestamp
                continue

            try:
                ts_float = float(ts_val)
            except (TypeError, ValueError) as e:
                print(f"⚠️ Skipping message with invalid ts `{ts_val}`: {e}")
                continue

            out.append({
                "ts":        ts_val,
                "ts_float":  ts_float,
                "user":      user,
                "user_name": user_name,
                "text":      text,
            })

        return Response(out, status=status.HTTP_200_OK)
