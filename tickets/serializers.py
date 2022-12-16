from datetime import datetime

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from django.db.models import Q
from tickets.models import Ticket, Route, ArrivalPoint, Order, City, Carriage, CarriageType, RouteToArrivalPoint
from users.models import Discount

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


class CitySerializer(ModelSerializer):

    class Meta:
        model = City
        fields = ('id', 'city_name', 'description')


class ArrivalPointSerializer(ModelSerializer):
    arrival_city = serializers.CharField(max_length=32, required=True)
    arrival_place = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = ArrivalPoint
        fields = ('id', 'arrival_city', 'arrival_place')

    def to_internal_value(self, data):
        if arrival_city := data.get('arrival_city'):
            try:
                data['arrival_city'] = City.objects.get(city_name=arrival_city)
            except City.DoesNotExist:
                raise serializers.ValidationError({'arrival_city': 'City does not exist'})
        return data


class CarriageTypeSerializer(ModelSerializer):
    class Meta:
        model = CarriageType
        fields = ('id', 'carriage_type_name', 'description')


class NestedArrivalPointSerializer(Serializer):
    arrival_point = serializers.CharField(max_length=32)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    arrival_time = serializers.DateTimeField(format=DATETIME_FORMAT, required=True)
    order = serializers.IntegerField(required=False, write_only=True)

    def validate_arrival_point_id(self, data):
        if ArrivalPoint.objects.filter(id=data):
            raise serializers.ValidationError('No arrival point with this id')
        return data

    def to_internal_value(self, data):
        super().to_internal_value(data)
        data['arrival_point'] = ArrivalPoint.objects.get(id=data['arrival_point'])
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        arrival_point_id = data['arrival_point']
        del data['arrival_point']
        data.update(ArrivalPointSerializer(instance=ArrivalPoint.objects.get(id=arrival_point_id)).data)
        return data


class RouteSerializer(ModelSerializer):
    departure_city = serializers.CharField(max_length=32)
    departure_time = serializers.DateTimeField(format=DATETIME_FORMAT)
    arrival_points = NestedArrivalPointSerializer(many=True, write_only=True)

    class Meta:
        model = Route
        fields = ('id', 'departure_city', 'departure_time', 'arrival_points')

    def to_internal_value(self, data):
        super().to_internal_value(data)
        if departure_city := data.get('departure_city'):
            try:
                data['departure_city'] = ArrivalPoint.objects.get(id=departure_city)
            except City.DoesNotExist:
                raise serializers.ValidationError({'departure_city': 'City does not exist'})
        points = data['arrival_points']

        if not points:
            return data
        if not all(points[i]['price'] <= points[i+1]['price'] and
                   datetime.fromisoformat(points[i]['arrival_time']) <= datetime.fromisoformat(points[i+1]['arrival_time']) for i in range(len(points) - 1)):
            raise serializers.ValidationError({'arrival_points': 'The order of arrival points is invalid, check time and price'})

        if datetime.strptime(points[0]['arrival_time'], DATETIME_FORMAT) <= datetime.strptime(data['departure_time'], DATETIME_FORMAT):
            raise serializers.ValidationError({'arrival_points': 'First arrival time is before the departure time'})

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        arrival_points = RouteToArrivalPoint.objects.filter(route=data['id'])
        nested_data = NestedArrivalPointSerializer(arrival_points, many=True).data
        data['arrival_points'] = nested_data
        data['departure_city'] = ArrivalPointSerializer(instance=ArrivalPoint.objects.get(id=data['departure_city'])).data
        carriages = list(instance.carriages.all())
        data['carriages'] = {}
        for carriage in carriages:
            tickets_carriage = Ticket.objects.filter(carriage=carriage)
            taken_seats = [ticket.seat_number for ticket in tickets_carriage]

            available_seats = carriage.seat_amount - len(taken_seats)
            if available_seats:
                data['carriages'][carriage.carriage_type.carriage_type_name] = {
                    'available_seats_amount': available_seats,
                    'price': arrival_points.order_by('-order').first().price
                }
        return data

    def create(self, validated_data):
        arrival_points = validated_data.pop('arrival_points')
        route = Route.objects.create(**validated_data)
        for order, point in enumerate(arrival_points):
            point['order'] = order + 1
            RouteToArrivalPoint.objects.create(route=route, **point)

        return route


class CarriageSerializer(ModelSerializer):

    class Meta:
        model = Carriage
        fields = ('id', 'carriage_type', 'seat_amount', 'route')

    def validate_seat_amount(self, data):
        if data > 100:
            raise serializers.ValidationError('Max seat amount is 100')
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        data['route'] = RouteSerializer(instance.route).data
        return data


class CarriageSeatsSerializer(ModelSerializer):

    class Meta:
        model = Carriage
        fields = ('id', 'carriage_type', 'seat_amount', 'route')

    def validate_seat_amount(self, data):
        if data > 100:
            raise serializers.ValidationError('Max seat amount is 100')
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        tickets_carriage = Ticket.objects.filter(carriage=instance)
        taken_seats = [ticket.seat_number for ticket in tickets_carriage]
        all_seats = range(1, instance.seat_amount + 1)

        available_seats = list(set(all_seats) - set(taken_seats))
        data['route'] = RouteSerializer(instance.route).data
        data['available_seats'] = available_seats
        return data


class TicketSerializer(ModelSerializer):

    class Meta:
        model = Ticket
        fields = ('id', 'departure_point', 'arrival_point', 'carriage', 'seat_number')

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if data.get('carriage').seat_amount < data.get('seat_number'):
            raise serializers.ValidationError({'seat_number': 'Seat number is not found in this carriage'})

        if Ticket.objects.filter(arrival_point=data['arrival_point'], carriage=data['carriage'], seat_number=data['seat_number']):
            raise serializers.ValidationError({'seat_number': 'This seat is not available'})

        if not (arrival_route_point := RouteToArrivalPoint.objects.filter(arrival_point=data['arrival_point'], route=data['carriage'].route).first()):
            raise serializers.ValidationError({'arrival_point': 'No such arrival point in the route'})

        if not (departure_route_point := RouteToArrivalPoint.objects.filter(arrival_point=data['departure_point'], route=data['carriage'].route).first()):
            departure_price = 0
            if not data['carriage'].route.departure_city == data.get('departure_point'):
                raise serializers.ValidationError({'departure_point': 'No such departure point in the route'})
        else:
            departure_price = departure_route_point.price
            if departure_route_point.order >= arrival_route_point.order:
                raise serializers.ValidationError({'arrival_point': 'Invalid order'})

        data['price'] = arrival_route_point.price - departure_price
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        data['carriage'] = CarriageSerializer(instance.carriage).data
        data['price'] = instance.price
        data['arrival_point'] = ArrivalPointSerializer(instance=instance.arrival_point).data
        data['departure_point'] = ArrivalPointSerializer(instance=instance.departure_point).data
        return data

    def create(self, validated_data):
        current_user = self.context['request'].user
        if not (exist_order := Order.objects.filter(order_status="pending", user=current_user)):
            order_info = {
                "user": current_user,
                "order_status": "pending",
                "total_price": validated_data.get('price')
            }
            order = Order.objects.create(**order_info)
        else:
            order = exist_order.first()
            order.total_price += validated_data.get('price')
            order.save()
        ticket = Ticket.objects.create(order=order, **validated_data)

        return ticket


class SearchRouteSerializer(Serializer):
    departure_city = serializers.CharField(required=True, max_length=32)
    arrival_city = serializers.CharField(required=False, write_only=True, max_length=32)
    departure_day = serializers.DateTimeField(required=False, write_only=True, input_formats=('%Y-%m-%d',))

    def validate_departure_city(self, data):
        if not City.objects.filter(city_name=data):
            raise serializers.ValidationError('City does not exist')
        return data

    def validate_arrival_city(self, data):
        if not City.objects.filter(city_name=data):
            raise serializers.ValidationError('City does not exist')
        return data

    def to_internal_value(self, data):
        super().to_internal_value(data)
        departure_city = data.get('departure_city')

        if not departure_city:
            raise serializers.ValidationError({'departure_city': 'This field is required.'})
        filtered_routes = Route.objects.filter(departure_city__arrival_city__city_name=departure_city)

        filtered_arrival_points = RouteToArrivalPoint.objects.filter(arrival_point__arrival_city__city_name=departure_city)

        for arrival_point in filtered_arrival_points:
            if arrival_point.order != RouteToArrivalPoint.objects.filter(route=arrival_point.route).count():
                filtered_routes |= Route.objects.filter(id=arrival_point.route.id)


        if departure_day_str := data.get('departure_day'):
            departure_day = datetime.strptime(departure_day_str, '%Y-%m-%d')
            filtered_routes = filtered_routes.filter(Q(routetoarrivalpoint__arrival_time__date=departure_day) | Q(departure_time__date=departure_day))


        if arrival_city := data.get('arrival_city'):
            routes_ids = RouteToArrivalPoint.objects.filter(arrival_point__arrival_city__city_name=arrival_city).values_list('route', flat=True)
            filtered_routes = filtered_routes.filter(id__in=routes_ids)

        return RouteSerializer(set(filtered_routes), many=True).data


class NestedOrderTicketSerializer(ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('id', 'departure_point', 'arrival_point', 'carriage', 'seat_number', 'price')


    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        data['arrival_point'] = ArrivalPointSerializer(instance=instance.arrival_point).data
        data['departure_point'] = ArrivalPointSerializer(instance=instance.departure_point).data
        return data

class OrderSerializer(ModelSerializer):

    class Meta:
        model = Order
        fields = ('id', 'order_status', 'ordered_tickets', 'total_price', 'user')

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        data['ordered_tickets'] = NestedOrderTicketSerializer(instance=instance.ordered_tickets, many=True).data
        return data


class OrderPatchSerializer(ModelSerializer):
    discount_id = serializers.IntegerField(required=False)

    class Meta:
        model = Order
        fields = ('id', 'order_status', 'discount_id')

    def validate_discount_id(self, data):
        if not Discount.objects.filter(id=data):
            raise serializers.ValidationError('No such discount')
        return data


class OrderBuySerializer(Serializer):
    discount_id = serializers.IntegerField(required=False)

    def validate_discount_id(self, data):
        if not Discount.objects.filter(id=data):
            raise serializers.ValidationError('No such discount')
        return data