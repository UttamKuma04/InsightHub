import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.cache import bump_tenant_cache_version
from apps.core.permissions import IsAnalystOrAdmin
from apps.review.serializers import ReviewRequestSerializer
from apps.review.services import approve_record, reject_record


logger = logging.getLogger(__name__)


class BaseReviewView(APIView):
    permission_classes = [IsAnalystOrAdmin]
    review_handler = None

    def post(self, request):
        serializer = ReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = self.review_handler(
                serializer.validated_data["record_type"],
                serializer.validated_data["record_id"],
                request.user,
            )
        except Exception:
            logger.exception(
                "Review action failed for %s#%s by user %s.",
                serializer.validated_data["record_type"],
                serializer.validated_data["record_id"],
                request.user.id,
            )
            raise
        bump_tenant_cache_version(request.user.tenant_id)
        return Response(
            {
                "record_type": record.RECORD_TYPE,
                "record_id": record.id,
                "status": _choice_value(record.status),
                "locked": record.locked,
            },
            status=status.HTTP_200_OK,
        )


class ApproveRecordView(BaseReviewView):
    review_handler = staticmethod(approve_record)


class RejectRecordView(BaseReviewView):
    review_handler = staticmethod(reject_record)


def _choice_value(value):
    return value.value if hasattr(value, "value") else value
