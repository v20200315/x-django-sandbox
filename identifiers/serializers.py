from rest_framework import serializers

from .models import DI


class DISerializer(serializers.ModelSerializer):
    class Meta:
        model = DI
        fields = ('id', 'value', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
