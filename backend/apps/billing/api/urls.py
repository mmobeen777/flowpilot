from django.urls import path
from .views import PlanListView, SubscriptionDetailView, SubscriptionUpgradeView

urlpatterns = [
    path("/plans", PlanListView.as_view(), name="plan-list"),
    path("/subscription", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("/subscription/upgrade", SubscriptionUpgradeView.as_view(), name="subscription-upgrade"),
]