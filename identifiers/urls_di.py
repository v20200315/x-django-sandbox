from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DIViewSet

router = DefaultRouter()
router.register(r'', DIViewSet, basename='di')

urlpatterns = [
    path('', include(router.urls)),
]
