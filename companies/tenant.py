from uuid import UUID

from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import CompanyMembership

HEADER = 'X-Company-ID'


def get_active_company_id(request):
    """
    Read X-Company-ID from request, validate UUID, and ensure the authenticated
    user has a membership in that company. Returns company_id (UUID).
    """
    raw = request.headers.get(HEADER)
    if not raw:
        raise ValidationError({HEADER: 'This header is required.'})

    try:
        company_id = UUID(raw)
    except ValueError:
        raise ValidationError({HEADER: 'Invalid UUID.'})

    if not CompanyMembership.objects.filter(
        user=request.user,
        company_id=company_id,
    ).exists():
        raise PermissionDenied('You do not belong to this company.')

    return company_id


def require_company_membership(request, required_roles=None):
    """
    Use in a view: company_id, membership = require_company_membership(request, required_roles=['owner', 'admin'])
    Returns (company_id, membership). If required_roles given, checks role.
    """
    company_id = get_active_company_id(request)
    membership = CompanyMembership.objects.get(user=request.user, company_id=company_id)
    if required_roles and membership.role not in required_roles:
        raise PermissionDenied(f'Required role: {required_roles}.')
    return company_id, membership
