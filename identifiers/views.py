from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import AI, DI
from .permissions import IsOwner
from .serializers import AISerializer, DISerializer


class AIPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AIViewSet(ModelViewSet):
    """
    CRUD for AI (Application Identifier) - base/reference data.
    All authenticated users can view the list.
    List is paginated.
    """

    queryset = AI.objects.all()
    serializer_class = AISerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AIPagination
    lookup_url_kwarg = 'id'


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
