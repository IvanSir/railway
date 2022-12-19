from datetime import datetime

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from django.db.models import Q
from tickets.models import Ticket, Route, ArrivalPoint, Order, City, Carriage, CarriageType, RouteToArrivalPoint
from tickets.sql_queries import select_query, custom_query, insert_query, update_query
from users.models import Discount

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


class CitySerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    city_name = serializers.CharField(max_length=32, required=True)
    description = serializers.CharField(max_length=255, required=False)



class ArrivalPointSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    arrival_city = serializers.CharField(max_length=32, required=True)
    arrival_place = serializers.CharField(max_length=255, required=True)


    def to_internal_value(self, data):
        super().to_internal_value(data)
        if arrival_city := data.get('arrival_city'):
            rows = select_query(table_name='tickets_city', fields=['id', ], where_clause={'city_name': arrival_city})
            if not rows:
                raise serializers.ValidationError({'arrival_city': 'City does not exist'})

            data['arrival_city'] = select_query(table_name='tickets_city', fields=['id', ], where_clause={'city_name': arrival_city})[0][0]

        return data


    def to_representation(self, instance):
        data = super().to_representation(instance)
        rows = select_query(table_name='tickets_city', fields=['city_name', ], where_clause={'id': instance.arrival_city})
        data['arrival_city'] = rows[0][0]
        return data


class CarriageTypeSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    carriage_type_name = serializers.CharField(max_length=32, required=True)
    description = serializers.CharField(max_length=255, required=False)



class NestedArrivalPointSerializer(Serializer):
    arrival_point = serializers.CharField(max_length=32)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    arrival_time = serializers.DateTimeField(format=DATETIME_FORMAT, required=True)
    order = serializers.IntegerField(required=False, write_only=True)


    def to_internal_value(self, data):
        super().to_internal_value(data)
        data['arrival_point'] = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': data['arrival_point']}
        )[0])
        return data

    def to_representation(self, instance):
        instance = RouteToArrivalPoint(*instance)
        data = super().to_representation(instance=instance)
        arrival_point_id = data['arrival_point']
        del data['arrival_point']
        ar = select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': arrival_point_id}
        )[0]

        ap = ArrivalPoint(*ar)
        data.update(ArrivalPointSerializer(instance=ap).data)
        return data


class RouteSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    departure_city = serializers.CharField(max_length=32)
    departure_time = serializers.DateTimeField(format=DATETIME_FORMAT)
    arrival_points = NestedArrivalPointSerializer(many=True, write_only=True)

    def to_internal_value(self, data):
        super().to_internal_value(data)
        if departure_city := data.get('departure_city'):
            data['departure_city'] = ArrivalPoint(*select_query(
                    table_name='tickets_arrivalpoint',
                    where_clause={'id': departure_city}
                )[0]
            )
        points = data['arrival_points']

        if not points:
            return data

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        arrival_points = select_query(
            table_name='tickets_routetoarrivalpoint',
            where_clause={'route_id': data['id']}
        )
        nested_data = NestedArrivalPointSerializer(arrival_points, many=True).data
        data['arrival_points'] = nested_data

        ar = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': data['departure_city']}
        )[0])
        data['departure_city'] = ArrivalPointSerializer(instance=ar).data

        cars = select_query(
            table_name='tickets_carriage',
            where_clause={'route_id': instance.id}
        )
        carriages = [Carriage(*car) for car in cars]
        data['carriages'] = {}

        price = custom_query(
            'SELECT price FROM tickets_routetoarrivalpoint ORDER BY "order" DESC'
        )[0]

        temp = {
            'available_seats_amount': 0,
            'price': price[0]
        }
        for carriage in carriages:
            tickets = select_query(
                table_name='tickets_ticket',
                where_clause={'carriage_id': carriage.id}
            )
            tickets_carriage = [Ticket(*ticket) for ticket in tickets]
            taken_seats = [ticket.seat_number for ticket in tickets_carriage]

            available_seats = carriage.seat_amount - len(taken_seats)
            temp['available_seats_amount'] += available_seats
        if temp['available_seats_amount']:
            data['carriages'] = temp
        return data

    def create(self, validated_data):
        arrival_points = validated_data.pop('arrival_points')
        validated_data['departure_city_id'] = validated_data['departure_city']
        validated_data.pop('departure_city')
        insert_query(
            table_name='tickets_route',
            fields=validated_data.keys(),
            values=validated_data.values()
        )

        route = Route(*custom_query('SELECT * FROM tickets_route ORDER BY id DESC')[0])

        for order, point in enumerate(arrival_points):
            point['order'] = order + 1
            fields_val = {'"route_id"': route.id, 'price': point['price'], 'arrival_time': point['arrival_time'], '"order"': point['order'], 'arrival_point_id': point['arrival_point'].id}
            insert_query(
                table_name='tickets_routetoarrivalpoint',
                fields=fields_val.keys(),
                values=fields_val.values()
            )

        return route


class CarriageSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    carriage_type = serializers.IntegerField()
    seat_amount = serializers.CharField(max_length=255, required=True)
    route = serializers.IntegerField()

    def validate_seat_amount(self, data):
        if data > 100:
            raise serializers.ValidationError('Max seat amount is 100')
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        route = Route(*select_query(
            table_name='tickets_route',
            where_clause={'id': instance.route}
        )[0])
        data['route'] = RouteSerializer(route).data
        return data


class CarriageSeatsSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    carriage_type = serializers.IntegerField()
    seat_amount = serializers.CharField(max_length=255, required=True)
    route = serializers.IntegerField()

    class Meta:
        model = Carriage
        fields = ('id', 'carriage_type', 'seat_amount', 'route')

    def validate_seat_amount(self, data):
        if data > 100:
            raise serializers.ValidationError('Max seat amount is 100')
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        tickets = select_query(
            table_name='tickets_ticket',
            where_clause={'carriage_id': instance.id}
        )
        tickets_carriage = [Ticket(*ticket) for ticket in tickets]
        taken_seats = [ticket.seat_number for ticket in tickets_carriage]
        all_seats = range(1, instance.seat_amount + 1)

        available_seats = list(set(all_seats) - set(taken_seats))
        rs = select_query(
            table_name='tickets_route',
            where_clause={'id': instance.route}
        )[0]
        route = Route(*rs)
        data['route'] = RouteSerializer(route).data
        data['available_seats'] = available_seats
        return data


class TicketSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    carriage = serializers.IntegerField()
    seat_number = serializers.IntegerField()
    departure_point = serializers.IntegerField()
    arrival_point = serializers.IntegerField()



    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        car = Carriage(*select_query(
            table_name='tickets_carriage',
            where_clause={'id': data['carriage']}
        )[0])
        if car.seat_amount < data.get('seat_number'):
            raise serializers.ValidationError({'seat_number': 'Seat number is not found in this carriage'})

        rows = select_query(
            table_name='tickets_ticket',
            where_clause={'arrival_point_id': data['arrival_point'], 'carriage_id':data['carriage'], 'seat_number':data['seat_number']}
        )
        if rows:
            raise serializers.ValidationError({'seat_number': 'This seat is not available'})



        row = select_query(
            table_name='tickets_routetoarrivalpoint',
            where_clause={'arrival_point_id': data['arrival_point'], 'route_id': car.route}
        )[0]
        if not (arrival_route_point := row):
            raise serializers.ValidationError({'arrival_point': 'No such arrival point in the route'})

        rowd = select_query(
            table_name='tickets_routetoarrivalpoint',
            where_clause={'arrival_point_id': data['departure_point'], 'route_id': car.route}
        )[0]

        if not (departure_route_point := rowd):
            departure_price = 0
        else:
            arrival_route_point = RouteToArrivalPoint(*row)
            departure_route_point = RouteToArrivalPoint(*rowd)
            departure_price = departure_route_point.price
            if departure_route_point.order >= arrival_route_point.order:
                raise serializers.ValidationError({'arrival_point': 'Invalid order'})

        data['price'] = arrival_route_point.price - departure_price
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        row = Carriage(*select_query(
            table_name='tickets_carriage',
            where_clause={'id': instance.carriage}
        )[0])
        data['carriage'] = CarriageSerializer(row).data
        data['price'] = instance.price

        rowap = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': instance.arrival_point}
        )[0])

        rowdp = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': instance.departure_point}
        )[0])
        data['arrival_point'] = ArrivalPointSerializer(instance=rowap).data
        data['departure_point'] = ArrivalPointSerializer(instance=rowdp).data
        return data

    def create(self, validated_data):
        current_user = self.context['request'].user

        filtered_orders = [Order(*row) for row in select_query(
            table_name='tickets_order',
            where_clause={'order_status': 'pending', 'user_id': current_user.id}
        )]

        if not (exist_order := filtered_orders):
            order_info = {
                "user": current_user,
                "order_status": "pending",
                "total_price": validated_data.get('price')
            }

            insert_query(
                table_name='tickets_order',
                fields=order_info.keys(),
                values=order_info.values()
            )
        else:
            order = exist_order[0]
            order.total_price += validated_data.get('price')
            update_query(
                table_name='tickets_order',
                set_fields={'total_price': order.total_price},
                where_clause={'id': order.id}
            )

        order = Order(*select_query(
            table_name='tickets_order',
            where_clause={'order_status': 'pending', 'user_id': current_user.id})[0])

        validated_data['"order"'] = order.id
        keys = ['carriage_id', 'seat_number', 'departure_point_id', 'arrival_point_id', 'price', 'order_id']

        insert_query(
            table_name='tickets_ticket',
            fields=keys,
            values=validated_data.values()
        )

        items = {}
        i = 0
        for val in validated_data.values():
            items[keys[i]] = val
            i += 1

        ticket = Ticket(*select_query(
            table_name='tickets_ticket',
            where_clause=items
        )[0])

        return ticket


class SearchRouteSerializer(Serializer):
    departure_city = serializers.CharField(required=True, max_length=32)
    arrival_city = serializers.CharField(required=False, write_only=True, max_length=32)
    departure_day = serializers.DateTimeField(required=False, write_only=True, input_formats=('%Y-%m-%d',))

    def validate_departure_city(self, data):
        rows = select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': data}
        )
        if not rows:
            raise serializers.ValidationError('Arrival point does not exist')
        return data

    def validate_arrival_city(self, data):
        rows = select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': data}
        )
        if not rows:
            raise serializers.ValidationError('Arrival point does not exist')
        return data

    def to_internal_value(self, data):
        super().to_internal_value(data)
        departure_city = data.get('departure_city')

        if not departure_city:
            raise serializers.ValidationError({'departure_city': 'This field is required.'})

        filtered_routes = [Route(*row) for row in select_query(
            table_name='tickets_route',
            where_clause={'departure_city_id': departure_city}
        )]

        filtered_arrival_points = [RouteToArrivalPoint(*row) for row in select_query(
            table_name='tickets_routetoarrivalpoint',
            where_clause={'arrival_point_id': departure_city}
        )]

        for arrival_point in filtered_arrival_points:
            if arrival_point.order != RouteToArrivalPoint.objects.filter(route=arrival_point.route).count():
                filtered_routes |= Route.objects.filter(id=arrival_point.route.id)


        if departure_day_str := data.get('departure_day'):
            departure_day = datetime.strptime(departure_day_str, '%Y-%m-%d')
            filtered_routes = filtered_routes.filter(Q(routetoarrivalpoint__arrival_time__date=departure_day) | Q(departure_time__date=departure_day))


        if arrival_city := data.get('arrival_city'):
            routes_ids = RouteToArrivalPoint.objects.filter(arrival_point=arrival_city).values_list('route', flat=True)
            filtered_routes = filtered_routes.filter(id__in=routes_ids)

        filtered_routes = filtered_routes.exclude(departure_time__date__lt=datetime.now().date())

        return RouteSerializer(set(filtered_routes), many=True).data


class NestedOrderTicketSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    carriage = serializers.IntegerField()
    seat_number = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        ap = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': instance.arrival_point}
        )[0])
        dp = ArrivalPoint(*select_query(
            table_name='tickets_arrivalpoint',
            where_clause={'id': instance.departure_point}
        )[0])

        data['arrival_point'] = ArrivalPointSerializer(instance=ap).data
        data['departure_point'] = ArrivalPointSerializer(instance=dp).data
        return data


class OrderSerializer(Serializer):
    id = serializers.IntegerField(read_only=True)
    order_status = serializers.CharField(max_length=32)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    user = serializers.CharField(max_length=255, required=True)

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        tickets = [Ticket(*row) for row in select_query(
            table_name='tickets_ticket',
            where_clause={'order_id': instance.id}
        )]
        data['ordered_tickets'] = NestedOrderTicketSerializer(instance=tickets, many=True).data
        return data


class OrderPatchSerializer(Serializer):
    discount_id = serializers.IntegerField(required=False)
    order_status = serializers.CharField(required=True)



class OrderBuySerializer(Serializer):
    discount_id = serializers.IntegerField(required=False)
