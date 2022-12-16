import decimal

import stripe
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from tickets.models import Ticket, ArrivalPoint, Route, Order, City, CarriageType, Carriage
from tickets.serializers import TicketSerializer, RouteSerializer, ArrivalPointSerializer, OrderSerializer, \
    CitySerializer, CarriageTypeSerializer, CarriageSerializer, SearchRouteSerializer, CarriageSeatsSerializer, \
    OrderPatchSerializer, OrderBuySerializer
from users.models import Discount


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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class ArrivalPointViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = ArrivalPoint.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ArrivalPointSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class CarriageTypeViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = CarriageType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CarriageTypeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class CarriageViewSet(viewsets.ModelViewSet, RailwayAPI):
    queryset = Carriage.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CarriageSerializer


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
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
        carriages = Carriage.objects.filter(route_id=pk)
        serializer = CarriageSeatsSerializer(carriages, many=True)
        return Response(data={'data': serializer.data}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class TicketsViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset.filter(user=request.user), many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        if not request.data.get('order_status'):
            raise serializers.ValidationError({'order_status': "This field is required"})

        if request.data.get('order_status') == 'success' and request.data.get('discount_id'):
            discount = Discount.objects.get(id=request.data.get('discount_id'))
            discount.usage_amount += 1
            discount.save()
        return self.update(request, *args, **kwargs)

    @action(methods=('GET',), detail=False, url_path=r'status/(?P<order_status>\w+)')
    def status_orders(self, request, order_status):
        if order_status not in [status_order[0] for status_order in Order.STATUS_CHOICES]:
            return Response('No such status', status=status.HTTP_400_BAD_REQUEST)
        filtered_orders = Order.objects.filter(order_status=order_status, user=request.user)
        return Response({'data': self.serializer_class(filtered_orders, many=True).data}, status=status.HTTP_200_OK)

    @action(methods=('POST', ), detail=True, url_path='buy')
    def buy_order(self, request, pk):
        order = Order.objects.get(pk=pk, user=request.user)
        price = order.total_price
        if not order or not price or order.order_status == 'success':
            return Response('No pending or fail orders', status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer_data := serializer.validated_data :

            discount = Discount.objects.get(id=serializer_data.get('discount_id'))
            if discount.user != request.user:
                return Response('User does not have this discount', status=status.HTTP_400_BAD_REQUEST)

            if discount.discount_type.discount_type_name == 'unlimited' or discount.usage_amount <= discount.discount_type.discount_limit:
                price = price - price * decimal.Decimal(discount.discount_type.discount_percent) / 100
            else:
                return Response('The number of uses of the discount exceeded the allowable amount', status=status.HTTP_400_BAD_REQUEST)


        payment_intent = stripe.PaymentIntent.create(
            amount=int(price * 100),
            currency="usd",
            payment_method_types=["card"],
        )
        return Response({'client_secret': payment_intent.get('client_secret')}, status=status.HTTP_200_OK)
