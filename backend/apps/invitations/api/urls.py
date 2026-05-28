from django.urls import path
from .views import InvitationListCreateView, AcceptInvitationView, RetrieveInvitationView

urlpatterns = [
    path("", InvitationListCreateView.as_view(), name="invitations"),
    path("/accept", AcceptInvitationView.as_view(), name="invitation-accept"),
    path("/retrieve/<str:id>", RetrieveInvitationView.as_view(), name="retrieve-invitation"),
]
