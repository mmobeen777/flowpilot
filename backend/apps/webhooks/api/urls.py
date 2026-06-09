from django.urls import path
from .views import WebhookEndpointListCreateView, WebhookEndpointDetailView, WebhookDeliveryListView, \
    WebhookRedeliverView

urlpatterns = [
    path("/endpoints", WebhookEndpointListCreateView.as_view(),name="webhook-endpoint-list"),
    path("/endpoints/<str:pk>", WebhookEndpointDetailView.as_view(), name="webhook-endpoint-detail"),
    path("/endpoints/<ste:pk>/deliveries", WebhookDeliveryListView.as_view(), name="webhook-delivery-list"),
    path("/deliveries/<ste:pk>/redeliver/", WebhookRedeliverView.as_view(), name="webhook-redeliver"),
]
