from django.urls import path

from .views import CreateCompanyView, MembershipsView, StaffCreateView

urlpatterns = [
    path('', CreateCompanyView.as_view()),
    path('staff/', StaffCreateView.as_view()),
    path('memberships/', MembershipsView.as_view()),
]
