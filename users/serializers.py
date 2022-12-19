from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from tickets.sql_queries import select_query
from users.models import User, Discount, DiscountType


class SignupUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=32)
    first_name = serializers.CharField(max_length=32, required=False)
    last_name = serializers.CharField(max_length=32, required=False)
    password = serializers.CharField(max_length=32)

    def validate_password(self, value: str) -> str:
        return make_password(value)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if 'first_name' not in data:
            data['first_name'] = ''
        if 'last_name' not in data:
            data['last_name'] = ''
        data['is_staff'] = False
        return data


class RetrieveUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=32)
    first_name = serializers.CharField(max_length=32)
    last_name = serializers.CharField(max_length=32)
    is_blocked = serializers.BooleanField()
    date_joined = serializers.DateTimeField()


class DiscountTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    discount_type_name = serializers.CharField(max_length=32)
    discount_percent = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_limit = serializers.IntegerField()

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)
        if data.get('discount_type_name') not in ('limited', 'permanent'):
            raise serializers.ValidationError({'discount_type_name': "Invalid Type name"})


        if data.get('discount_type_name') == 'limited' and not data.get('discount_limit'):
            raise serializers.ValidationError({'discount_limit': "Provide limit for discount if you set limited type"})

        if data.get('discount_type_name') == 'permanent' and data.get('discount_limit'):
            internal_data.pop('discount_limit')

        return internal_data


class DiscountSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    discount_type = serializers.CharField(max_length=32)
    user = serializers.IntegerField()
    usage_amount = serializers.CharField(max_length=32, required=False)


    def to_representation(self, instance):
        data = super().to_representation(instance)

        dis_types = select_query(
            table_name='users_discounttype',
            where_clause={'id': instance.discount_type}
        )[0]

        data['discount_type'] = DiscountTypeSerializer(instance=DiscountType(*dis_types)).data

        return data

