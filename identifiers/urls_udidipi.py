from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_udidipi import UDIDIPIViewSet

router = DefaultRouter()
router.register(r'', UDIDIPIViewSet, basename='udidipi')

urlpatterns = [
    path('', include(router.urls)),
]
