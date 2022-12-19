from datetime import datetime

from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from tickets.sql_queries import select_query, insert_query
from users.models import User, Discount, DiscountType
from users.serializers import RetrieveUserSerializer, SignupUserSerializer, DiscountSerializer, DiscountTypeSerializer


# DONE
class UserViewSet(viewsets.GenericViewSet,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  ):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = RetrieveUserSerializer
    serializer_action_classes = {
        'signup': SignupUserSerializer,
        'retrieve': RetrieveUserSerializer,
        'list': RetrieveUserSerializer
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, super().serializer_class)

    @action(methods=('POST',), detail=False, permission_classes=(AllowAny,))
    def signup(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        data.update({'is_superuser': False, 'is_staff': False, 'is_active': True, 'date_joined': datetime.now(), 'is_blocked': False})

        try:
            insert_query(
            table_name='users_user',
            fields=data.keys(),
            values=data.values()
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        ser_data = serializer.data
        ser_data.pop('password')
        return Response(ser_data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='users_user',
        )
        users = [User(*row) for row in rows]
        serializer = self.get_serializer(users, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


# DONE
class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = DiscountSerializer

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='users_discount',
            where_clause={'user_id': request.user.id}
        )
        discounts = [Discount(*row) for row in rows]
        serializer = self.get_serializer(discounts, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='users_discount',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such discount type')
        d = Discount(*rows[0])
        serializer = self.get_serializer(d)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        fk_changed = [f'{field}_id' for field in data.keys()]
        data.update({'usage_amount': 0})
        fk_changed.append('usage_amount')

        insert_query(
            table_name='users_discount',
            fields=fk_changed,
            values=data.values()
        )

        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)


# DONE
class DiscountTypeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin):
    queryset = DiscountType.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = DiscountTypeSerializer

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='users_discounttype'
        )
        discountst = [DiscountType(*row) for row in rows]
        serializer = self.get_serializer(discountst, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='users_discounttype',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such discount type')
        dt = DiscountType(*rows[0])
        serializer = self.get_serializer(dt)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        insert_query(
            table_name='users_discounttype',
            fields=serializer.validated_data.keys(),
            values=serializer.validated_data.values()
        )
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)