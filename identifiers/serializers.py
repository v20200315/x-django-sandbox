from rest_framework import serializers

from .models import AI, DI, UDIDIPI, UDIDIPIAIValue, UDIDIPIDILink


class AISerializer(serializers.ModelSerializer):
    class Meta:
        model = AI
        fields = ('id', 'code', 'description', 'format_spec', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class DISerializer(serializers.ModelSerializer):
    class Meta:
        model = DI
        fields = ('id', 'value', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class UDIDIPIAIValueInputSerializer(serializers.Serializer):
    """Single AI value input."""

    ai_id = serializers.UUIDField()
    value = serializers.CharField(max_length=255)


class UDIDIPICreateSerializer(serializers.Serializer):
    """Input for creating UDI-DI-PI."""

    di_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text='One or more DI IDs',
    )
    ai_values = serializers.ListField(
        child=UDIDIPIAIValueInputSerializer(),
        min_length=1,
        help_text='List of {ai_id, value}',
    )

    def validate_di_ids(self, value):
        request = self.context.get('request')
        if not request or not request.user:
            return value
        user_di_ids = set(
            DI.objects.filter(owner=request.user).values_list('id', flat=True)
        )
        invalid = set(value) - user_di_ids
        if invalid:
            raise serializers.ValidationError(
                f'Invalid or inaccessible DI IDs: {list(invalid)}'
            )
        return value

    def validate_ai_values(self, value):
        ai_ids = [item['ai_id'] for item in value]
        existing_ais = set(AI.objects.filter(id__in=ai_ids).values_list('id', flat=True))
        invalid = set(ai_ids) - existing_ais
        if invalid:
            raise serializers.ValidationError(
                f'Invalid AI IDs: {list(invalid)}'
            )
        return value


class UDIDIPIAIValueSerializer(serializers.ModelSerializer):
    ai_code = serializers.CharField(source='ai.code', read_only=True)
    ai_description = serializers.CharField(source='ai.description', read_only=True)

    class Meta:
        model = UDIDIPIAIValue
        fields = ('ai_id', 'ai_code', 'ai_description', 'value')


class UDIDIPIDILinkSerializer(serializers.ModelSerializer):
    di_value = serializers.CharField(source='di.value', read_only=True)

    class Meta:
        model = UDIDIPIDILink
        fields = ('di_id', 'di_value', 'order')


class UDIDIPISerializer(serializers.ModelSerializer):
    dis = UDIDIPIDILinkSerializer(
        source='udidipidilink_set', many=True, read_only=True
    )
    ai_values = UDIDIPIAIValueSerializer(
        source='udidipiaivalue_set', many=True, read_only=True
    )

    class Meta:
        model = UDIDIPI
        fields = (
            'id', 'generated_code', 'dis', 'ai_values',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'generated_code', 'created_at', 'updated_at')
