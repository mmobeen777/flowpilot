from django.urls import path
from .views import UsageView, QuotaView

urlpatterns = [
    path("/usage", UsageView.as_view(), name="usage"),
    path("/quota", QuotaView.as_view(), name="quota"),
]
