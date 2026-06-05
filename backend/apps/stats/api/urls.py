from django.urls import path
from .views import UsageSummaryView, DailyUsageView, QuotaTrendView, TopAPIKeysView, PeakUsageView, MonthlyTotalsView, \
    ExportDetailView, ExportDownloadView, ExportListCreateView


urlpatterns = [
    path("/summary", UsageSummaryView.as_view(), name="analytics-summary"),
    path("/daily-usage", DailyUsageView.as_view(), name="analytics-daily"),
    path("/quota-trend", QuotaTrendView.as_view(), name="analytics-quota-trend"),
    path("/top-key", TopAPIKeysView.as_view(), name="analytics-top-keys"),
    path("/peak-usage", PeakUsageView.as_view(), name="analytics-peak"),
    path("/monthly-usage", MonthlyTotalsView.as_view(), name="analytics-monthly"),
    path("/exports/", ExportListCreateView.as_view(), name="export-list-create"),
    path("/exports/<str:pk>", ExportDetailView.as_view(), name="export-detail"),
    path("/exports/<str:pk>/download", ExportDownloadView.as_view(), name="export-download")
]
