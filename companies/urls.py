from django.urls import path

from .views import CreateCompanyView, StaffCreateView

urlpatterns = [
    path('', CreateCompanyView.as_view()),  # POST /api/v1/companies/
    path(
        'staff/', StaffCreateView.as_view()
    ),  # POST /api/v1/companies/staff/ (uses X-Company-ID)
]
