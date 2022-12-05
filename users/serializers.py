from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from users.models import User, Discount, DiscountType


class SignupUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, max_length=255, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')

    def validate_password(self, value: str) -> str:
        """
        Hash value passed by user.

        :param value: password of a user
        :return: a hashed version of the password
        """
        return make_password(value)


class RetrieveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_blocked', 'date_joined')


class DiscountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountType
        fields = ('id', 'discount_type_name', 'discount_percent', 'discount_limit')

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        if data.get('discount_type_name') == 'limited' and not data.get('discount_limit'):
            raise serializers.ValidationError({'discount_limit': "Provide limit for discount if you set limited type"})

        if data.get('discount_type_name') == 'permanent' and data.get('discount_limit'):
            internal_data.pop('discount_limit')

        return internal_data


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ('id', 'discount_type', 'user')
