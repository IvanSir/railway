import datetime
import decimal

import pytz
import stripe
from rest_framework import status, viewsets, serializers, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response

from tickets.models import Ticket, ArrivalPoint, Route, Order, City, CarriageType, Carriage
from tickets.serializers import TicketSerializer, RouteSerializer, ArrivalPointSerializer, OrderSerializer, \
    CitySerializer, CarriageTypeSerializer, CarriageSerializer, SearchRouteSerializer, CarriageSeatsSerializer, \
    OrderPatchSerializer, OrderBuySerializer
from tickets.sql_queries import update_query, delete_query, select_query, insert_query, custom_query
from users.models import Discount, DiscountType


class RailwayAPI:
    permission_action_classes = {
        'list': (AllowAny,),
        'create': (IsAdminUser,),
        'update': (IsAdminUser,),
        'partial_update': (IsAdminUser,),
        'retrieve': (AllowAny,),
        'destroy': (IsAdminUser,),
    }
    serializer_action_classes = {}

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, super().serializer_class)

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_action_classes[self.action]]
        except KeyError:
            if self.action:
                action_func = getattr(self, self.action, {})
                action_func_kwargs = getattr(action_func, 'kwargs', {})
                permission_classes = action_func_kwargs.get('permission_classes')
            else:
                permission_classes = None

            return [permission() for permission in (permission_classes or self.permission_classes)]


class CityViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = City.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CitySerializer

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial', False)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_query(
            table_name='tickets_city',
            set_fields=serializer.data,
            where_clause=kwargs
        )
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        delete_query(
            table_name='tickets_city',
            where_clause=kwargs
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_city',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such city')
        city = City(*rows[0])
        serializer = self.get_serializer(city)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_city',
        )
        cities = [City(*row) for row in rows]
        serializer = self.get_serializer(cities, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        insert_query(
            table_name='tickets_city',
            fields=serializer.data.keys(),
            values=serializer.data.values()
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ArrivalPointViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin, RailwayAPI):
    queryset = ArrivalPoint.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ArrivalPointSerializer

    def destroy(self, request, *args, **kwargs):
        delete_query(
            table_name='tickets_arrivalpoint',
            where_clause=kwargs
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_arrivalpoint',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such arrival point')
        ap = ArrivalPoint(*rows[0])
        serializer = self.get_serializer(ap)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_arrivalpoint',
        )
        aps = [ArrivalPoint(*row) for row in rows]
        serializer = self.get_serializer(aps, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fk_changed = [field for field in serializer.data.keys()]
        fk_changed[0] = 'arrival_city_id'

        city_id = select_query(table_name='tickets_city', fields=['id', ], where_clause={'city_name': serializer.data['arrival_city']})[0][0]
        val_changed = [field for field in serializer.data.values()]
        val_changed[0] = city_id

        insert_query(
            table_name='tickets_arrivalpoint',
            fields=fk_changed,
            values=val_changed
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CarriageTypeViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = CarriageType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CarriageTypeSerializer

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial', False)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_query(
            table_name='tickets_carriagetype',
            set_fields=serializer.data,
            where_clause=kwargs
        )
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        delete_query(
            table_name='tickets_carriagetype',
            where_clause=kwargs
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_carriagetype',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such carriage type')
        cartype = CarriageType(*rows[0])
        serializer = self.get_serializer(cartype)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_carriagetype',
        )
        cities = [CarriageType(*row) for row in rows]
        serializer = self.get_serializer(cities, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        insert_query(
            table_name='tickets_carriagetype',
            fields=serializer.data.keys(),
            values=serializer.data.values()
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CarriageViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = Carriage.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CarriageSerializer

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_carriage',
        )
        cr = [Carriage(*row) for row in rows]
        serializer = self.get_serializer(cr, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class RouteViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RouteSerializer
    serializer_action_classes = {
        'search_route': SearchRouteSerializer
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    @action(methods=('POST', ), detail=False, url_path='search')
    def search_route(self, request):
        serializer = SearchRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'data': serializer.validated_data}, status=status.HTTP_200_OK)

    @action(methods=('GET', ), detail=True, url_path='carriages')
    def get_carriages(self, request, pk):
        carriages = select_query(
            table_name='tickets_carriage',
            where_clause={'route_id': pk}
        )

        serializer = CarriageSeatsSerializer([Carriage(*car) for car in carriages], many=True)
        return Response(data={'data': serializer.data}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        query = f"SELECT * FROM tickets_route WHERE departure_time>'{datetime.datetime.now().replace(tzinfo=pytz.UTC)}'"
        rows = custom_query(query)
        r = [Route(*row) for row in rows]
        serializer = self.get_serializer(r, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_route',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such route')
        route = Route(*rows[0])
        serializer = self.get_serializer(route)
        return Response(serializer.data)

class TicketsViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializer

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_ticket'
        )
        tickets = [Ticket(*row) for row in rows]
        serializer = self.get_serializer(tickets, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_ticket',
            where_clause=kwargs
        )
        if not rows:
            return Response('No such ticket')
        ticket = Ticket(*rows[0])
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    serializer_action_classes = {
        'partial_update' : OrderPatchSerializer,
        'buy_order': OrderBuySerializer
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    def list(self, request, *args, **kwargs):
        rows = select_query(
            table_name='tickets_order',
            where_clause={'user_id': request.user.id}
        )
        orders = [Order(*row) for row in rows]
        serializer = self.get_serializer(orders, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        if not request.data.get('order_status'):
            raise serializers.ValidationError({'order_status': "This field is required"})

        if request.data.get('order_status') == 'success' and request.data.get('discount_id'):
            discount = Discount(*select_query(
                table_name='users_discount',
                where_clause={'id': request.data.get('discount_id')}
            )[0])

            discount.usage_amount += 1
            update_query(
                table_name='users_discount',
                set_fields={'usage_amount': discount.usage_amount},
                where_clause={'id': discount.id}

            )

            dt = DiscountType(*select_query(
                table_name='users_discounttype',
                where_clause={'id': discount.discount_type}
            )[0])

            if dt.discount_type_name == 'limited' and discount.usage_amount >= dt.discount_limit:
                delete_query(
                    table_name='users_discount',
                    where_clause={'id': discount.id}
                )
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial', False)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_query(
            table_name='tickets_order',
            set_fields=serializer.data,
            where_clause=kwargs
        )
        return Response(serializer.data)

    @action(methods=('GET',), detail=False, url_path=r'status/(?P<order_status>\w+)')
    def status_orders(self, request, order_status):
        if order_status not in [status_order[0] for status_order in Order.STATUS_CHOICES]:
            return Response('No such status', status=status.HTTP_400_BAD_REQUEST)

        filtered_orders = [Order(*row) for row in select_query(
            table_name='tickets_order',
            where_clause={'order_status': order_status, 'user_id': request.user.id}
        )]
        return Response({'data': self.serializer_class(filtered_orders, many=True).data}, status=status.HTTP_200_OK)

    @action(methods=('POST', ), detail=True, url_path='buy')
    def buy_order(self, request, pk):
        order = Order(*select_query(
            table_name='tickets_order',
            where_clause={'user_id': request.user.id, 'id': pk}
        )[0])
        price = order.total_price
        if not order or not price or order.order_status == 'success':
            return Response('No pending or fail orders', status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer_data := serializer.validated_data :

            discount = Discount(*select_query(
                table_name='users_discount',
                where_clause={'id': serializer_data.get('discount_id')}
            )[0])

            dt = DiscountType(*select_query(
                table_name='users_discounttype',
                where_clause={'id': discount.discount_type}
            )[0])

            if discount.user != request.user:
                return Response('User does not have this discount', status=status.HTTP_400_BAD_REQUEST)

            if dt.discount_type_name == 'permanent' or discount.usage_amount < dt.discount_limit:
                price = price - price * decimal.Decimal(dt.discount_percent) / 100
            else:
                return Response('The number of uses of the discount exceeded the allowable amount', status=status.HTTP_400_BAD_REQUEST)


        payment_intent = stripe.PaymentIntent.create(
            amount=int(price * 100),
            currency="usd",
            payment_method_types=["card"],
        )
        return Response({'client_secret': payment_intent.get('client_secret')}, status=status.HTTP_200_OK)
