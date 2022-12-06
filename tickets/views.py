from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from tickets.models import Ticket, ArrivalPoint, Route, Order, City, CarriageType, Carriage
from tickets.serializers import TicketSerializer, RouteSerializer, ArrivalPointSerializer, OrderSerializer, \
    CitySerializer, CarriageTypeSerializer, CarriageSerializer, SearchRouteSerializer


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

    @action(methods=('GET',), detail=True, url_path='available_seats')
    def available_seats(self, request, pk):
        carriage = Carriage.objects.get(pk=pk)
        tickets_carriage = Ticket.objects.filter(carriage=carriage)
        taken_seats = [ticket.seat_number for ticket in tickets_carriage]
        all_seats = range(1, carriage.seat_amount + 1)

        available_seats = list(set(all_seats) - set(taken_seats))
        return Response({'data': available_seats}, status=status.HTTP_200_OK)

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
        serializer = CarriageSerializer(carriages, many=True)
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

    @action(methods=('GET',), detail=False, url_path=r'(?P<order_status>\w+)')
    def status_orders(self, request, order_status):
        if order_status not in [status_order[0] for status_order in Order.STATUS_CHOICES]:
            return Response('No such status', status=status.HTTP_400_BAD_REQUEST)
        filtered_orders = Order.objects.filter(order_status=order_status)
        return Response({'data': self.serializer_class(filtered_orders, many=True).data}, status=status.HTTP_200_OK)
