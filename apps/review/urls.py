from django.urls import path

from apps.review.views import ApproveRecordView, RejectRecordView

urlpatterns = [
    path("approve", ApproveRecordView.as_view(), name="review-approve"),
    path("reject", RejectRecordView.as_view(), name="review-reject"),
]

