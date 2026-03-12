from django.db import transaction
from rest_framework import serializers

from accounts.models import User

from .models import Company, CompanyMembership, CompanyRole


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'created_at')
        read_only_fields = fields


class CompanyMembershipSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ('id', 'company', 'role', 'created_at')
        read_only_fields = fields


class CreateCompanySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def validate_name(self, value):
        if Company.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                'A company with this name already exists.'
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        company = Company.objects.create(name=validated_data['name'])
        CompanyMembership.objects.create(
            user=request.user,
            company=company,
            role=CompanyRole.OWNER,
        )
        return company


class StaffCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=CompanyRole.choices, default=CompanyRole.STAFF
    )

    @transaction.atomic
    def create(self, validated_data):
        company = self.context['company']
        email = validated_data['email']
        password = validated_data['password']
        role = validated_data['role']

        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_password(password)
            user.save(update_fields=('password',))

        membership, created = CompanyMembership.objects.get_or_create(
            user=user,
            company=company,
            defaults={'role': role},
        )
        if not created and membership.role != role:
            membership.role = role
            membership.save(update_fields=('role',))

        return membership
