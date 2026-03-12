from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CreateCompanyView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ResetPasswordView,
    StaffCreateView,
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('me/', MeView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    # Company endpoints
    path('companies/', CreateCompanyView.as_view()),
    path('companies/staff/', StaffCreateView.as_view()),
]
