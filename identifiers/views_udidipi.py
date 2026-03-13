from django.db import transaction
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import AI, DI, UDIDIPI, UDIDIPIAIValue, UDIDIPIDILink
from .permissions import IsOwner
from .serializers import (
    UDIDIPICreateSerializer,
    UDIDIPISerializer,
)
from .services import generate_udidipi_code


class UDIDIPIPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UDIDIPIViewSet(ModelViewSet):
    """
    CRUD for UDI-DI-PI records.
    Users can only access their own records.
    Create: select DIs + AIs with values; backend generates code.
    """

    serializer_class = UDIDIPISerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = UDIDIPIPagination
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return UDIDIPI.objects.filter(owner=self.request.user).prefetch_related(
            'udidipidilink_set__di',
            'udidipiaivalue_set__ai',
        )

    def create(self, request, *args, **kwargs):
        create_serializer = UDIDIPICreateSerializer(
            data=request.data,
            context={'request': request},
        )
        create_serializer.is_valid(raise_exception=True)
        data = create_serializer.validated_data

        di_ids = data['di_ids']
        ai_values = data['ai_values']

        # Fetch DIs (order preserved)
        dis = list(DI.objects.filter(id__in=di_ids).order_by('id'))
        di_order = {did: i for i, did in enumerate(di_ids)}
        dis_sorted = sorted(dis, key=lambda d: di_order.get(d.id, 999))

        # Build AI (code, value) pairs
        ai_map = {str(a.id): a for a in AI.objects.filter(id__in=[av['ai_id'] for av in ai_values])}
        ai_pairs = [
            (ai_map[str(av['ai_id'])].code, av['value'])
            for av in ai_values
            if str(av['ai_id']) in ai_map
        ]

        # Generate code
        di_values = [d.value for d in dis_sorted]
        generated_code = generate_udidipi_code(di_values, ai_pairs)

        with transaction.atomic():
            udidipi = UDIDIPI.objects.create(
                owner=request.user,
                generated_code=generated_code,
            )
            for i, di in enumerate(dis_sorted):
                UDIDIPIDILink.objects.create(
                    udidipi=udidipi,
                    di=di,
                    order=i,
                )
            for av in ai_values:
                UDIDIPIAIValue.objects.create(
                    udidipi=udidipi,
                    ai_id=av['ai_id'],
                    value=av['value'],
                )

        serializer = self.get_serializer(udidipi)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        create_serializer = UDIDIPICreateSerializer(
            data=request.data,
            context={'request': request},
        )
        create_serializer.is_valid(raise_exception=True)
        data = create_serializer.validated_data

        di_ids = data['di_ids']
        ai_values = data['ai_values']

        dis = list(DI.objects.filter(id__in=di_ids).order_by('id'))
        di_order = {did: i for i, did in enumerate(di_ids)}
        dis_sorted = sorted(dis, key=lambda d: di_order.get(d.id, 999))

        ai_map = {str(a.id): a for a in AI.objects.filter(id__in=[av['ai_id'] for av in ai_values])}
        ai_pairs = [
            (ai_map[str(av['ai_id'])].code, av['value'])
            for av in ai_values
            if str(av['ai_id']) in ai_map
        ]

        di_values = [d.value for d in dis_sorted]
        generated_code = generate_udidipi_code(di_values, ai_pairs)

        with transaction.atomic():
            instance.generated_code = generated_code
            instance.save()
            instance.udidipidilink_set.all().delete()
            instance.udidipiaivalue_set.all().delete()
            for i, di in enumerate(dis_sorted):
                UDIDIPIDILink.objects.create(
                    udidipi=instance,
                    di=di,
                    order=i,
                )
            for av in ai_values:
                UDIDIPIAIValue.objects.create(
                    udidipi=instance,
                    ai_id=av['ai_id'],
                    value=av['value'],
                )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
