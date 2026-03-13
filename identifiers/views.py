from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import DI
from .permissions import IsOwner
from .serializers import DISerializer


class DIPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DIViewSet(ModelViewSet):
    """
    CRUD for DI (Device Identifier) records.
    Users can only access records they created.
    List is paginated.
    """

    serializer_class = DISerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = DIPagination
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return DI.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
