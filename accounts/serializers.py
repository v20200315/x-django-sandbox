from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from companies.models import Company

from .models import CompanyMembership, CompanyRole, User


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'created_at')
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ('id', 'company', 'role', 'created_at')
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'date_joined', 'memberships')
        read_only_fields = ('id', 'email', 'date_joined', 'memberships')


# ---- Option 2: Register = person only (no company) ----
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = serializers.EmailField()

    def validate(self, attrs):
        return super().validate(attrs)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
