from django.db import models


class Ticket(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat_number = models.IntegerField()
    order = models.ForeignKey('tickets.Order', on_delete=models.SET_NULL, related_name='ordered_tickets', blank=True, null=True)
    carriage = models.ForeignKey('tickets.Carriage', on_delete=models.CASCADE, related_name='tickets')
    departure_point = models.ForeignKey('tickets.ArrivalPoint', on_delete=models.CASCADE)
    arrival_point = models.ForeignKey('tickets.ArrivalPoint', on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        return f'{self.id} - ({self.departure_point}:{self.arrival_point}) - seat:{self.seat_number}, price:{self.price}'


class ArrivalPoint(models.Model):
    arrival_city = models.ForeignKey('tickets.City', on_delete=models.CASCADE, related_name='arrivals')
    arrival_place = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.arrival_city.city_name} - {self.arrival_place}'


class Route(models.Model):
    departure_city = models.ForeignKey('tickets.ArrivalPoint', on_delete=models.CASCADE, related_name='departures')
    departure_time = models.DateTimeField(blank=False, null=False)

    def __str__(self):
        return f'{self.id} - From {self.departure_city} at {self.departure_time.strftime("%Y-%m-%d %H:%M")}'


class RouteToArrivalPoint(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    arrival_point = models.ForeignKey(ArrivalPoint, on_delete=models.CASCADE)
    order = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    arrival_time = models.DateTimeField()

    def __str__(self):
        return f'{self.id} - {self.route.departure_city} to {self.arrival_point} at {self.arrival_time.strftime("%Y-%m-%d %H:%M")} for {self.price} (order - {self.order})'


class CarriageType(models.Model):
    CARRIAGE_CHOICES = (
        ('seated', 'Seated'),
        ('coupe', 'Coupe'),
        ('platzkart', 'Platzkart')
    )
    carriage_type_name = models.CharField(max_length=25, choices=CARRIAGE_CHOICES)
    description = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.carriage_type_name}'


class Carriage(models.Model):
    carriage_type = models.ForeignKey('tickets.CarriageType', on_delete=models.CASCADE)
    seat_amount = models.IntegerField()
    route = models.ForeignKey('tickets.Route', on_delete=models.CASCADE, related_name='carriages')

    def __str__(self):
        return f'{self.id} - {self.carriage_type.carriage_type_name}, seats - {self.seat_amount}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('fail', 'Fail'),
        ('success', 'Success'),
        ('pending', 'Pending'),
    )
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')

    def __str__(self):
        return f'{self.id} - {self.user.username}/{self.total_price}/{self.order_status}'


class City(models.Model):
    city_name = models.CharField(max_length=32, unique=True)
    description = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.city_name}'
