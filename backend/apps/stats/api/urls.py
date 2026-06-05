from django.urls import path
from .views import UsageSummaryView, DailyUsageView, QuotaTrendView, TopAPIKeysView, PeakUsageView, MonthlyTotalsView


urlpatterns = [
    path("/summary", UsageSummaryView.as_view(), name="analytics-summary"),
    path("/daily-usage", DailyUsageView.as_view(), name="analytics-daily"),
    path("/quota-trend", QuotaTrendView.as_view(), name="analytics-quota-trend"),
    path("/top-key", TopAPIKeysView.as_view(), name="analytics-top-keys"),
    path("/peak-usage", PeakUsageView.as_view(), name="analytics-peak"),
    path("/monthly-usage", MonthlyTotalsView.as_view(), name="analytics-monthly"),
]