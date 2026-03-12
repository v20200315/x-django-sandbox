from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, CompanyRole
from .serializers import (
    CompanyMembershipSerializer,
    CreateCompanySerializer,
    StaffCreateSerializer,
)
from .tenant import require_company_membership


class MembershipsView(APIView):
    """
    Get current user's company memberships.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CompanyMembershipSerializer(many=True)},
        summary='Get current user company memberships',
    )
    def get(self, request):
        memberships = request.user.memberships.all()
        serializer = CompanyMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class CreateCompanyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CreateCompanySerializer,
        responses={201: OpenApiResponse(description='Company created, user is owner')},
        summary='Create a company (you become owner)',
    )
    def post(self, request):
        serializer = CreateCompanySerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response(
            {'id': str(company.id), 'name': company.name},
            status=status.HTTP_201_CREATED,
        )


class StaffCreateView(APIView):
    """
    Create staff in the active company.
    Requires header: X-Company-ID
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StaffCreateSerializer,
        responses={201: OpenApiResponse(description='Staff membership created')},
        summary='Create staff in active company (header: X-Company-ID)',
    )
    def post(self, request):
        company_id, _membership = require_company_membership(
            request,
            required_roles=[CompanyRole.OWNER, CompanyRole.ADMIN],
        )

        company = Company.objects.get(id=company_id)

        serializer = StaffCreateSerializer(
            data=request.data,
            context={'request': request, 'company': company},
        )
        serializer.is_valid(raise_exception=True)
        m = serializer.save()

        return Response(
            {
                'membership_id': str(m.id),
                'user_email': m.user.email,
                'company_id': str(m.company_id),
                'role': m.role,
            },
            status=status.HTTP_201_CREATED,
        )
