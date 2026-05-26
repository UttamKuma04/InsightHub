from rest_framework import generics
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.core.cache import get_cached, set_cached, tenant_cache_key
from apps.core.permissions import IsAnalystOrAdmin


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAnalystOrAdmin]

    def get_queryset(self):
        return AuditLog.objects.filter(user__tenant=self.request.user.tenant).select_related("user")

    def list(self, request, *args, **kwargs):
        cache_key = tenant_cache_key(request.user.tenant_id, "audit-list")
        cached = get_cached(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        set_cached(cache_key, response.data)
        return response
