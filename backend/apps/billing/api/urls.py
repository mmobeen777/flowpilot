from django.urls import path

from .web_hook import stripe_webhook
from .views import PlanListView, SubscriptionDetailView, SubscriptionUpgradeView, UpcomingInvoiceView

urlpatterns = [
    path("/plans", PlanListView.as_view(), name="plan-list"),
    path("/subscription", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("/subscription/upgrade", SubscriptionUpgradeView.as_view(), name="subscription-upgrade"),
    path("/invoice/upcoming", UpcomingInvoiceView.as_view(), name="upcoming-invoice"),
    path("/webhook/stripe", stripe_webhook, name="stripe-webhook")
]